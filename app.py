import tkinter as tki
import tkinter.ttk as ttk
import time
import json
import datetime
from tkinter import font
from plyer import notification
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

#Thanks to Gemini(Generative AI) fix some library error that I encountered
plyer_available = True
matplotlib_available = True

# IO Data file of JSON constant
DATA_FILE = "focusflow_data.json"

# --- Global Variables and Data Structures ---
# Defines the core data structures (lists, dictionaries) with global variables for managing state UI...
tasks = []
daily_logs = {}
timers = [
    {'id': 0, 'name': 'Work/Study', 'elapsed': 0, 'running': False, 'start_time': None, 'enabled': True, 'widgets': {}, 'last_saved_elapsed': 0},
    {'id': 1, 'name': 'Rest/Entertain', 'elapsed': 0, 'running': False, 'start_time': None, 'enabled': True, 'widgets': {}, 'last_saved_elapsed': 0},
    {'id': 2, 'name': 'Sleep/Eat', 'elapsed': 0, 'running': False, 'start_time': None, 'enabled': True, 'widgets': {}, 'last_saved_elapsed': 0},
    {'id': 3, 'name': 'Others', 'elapsed': 0, 'running': False, 'start_time': None, 'enabled': True, 'widgets': {}, 'last_saved_elapsed': 0}
]

user_name = "Friend"
active_frame = None
new_todo_form_frame = None
done_list_display_frame = None
pending_area_frame = None
prog_bar_frame = None
prog_bar = None
prog_lbl = None
confirm_widgets_map = {}
task_name_var = None
task_content_text = None
start_hour_var = None
start_minute_var = None
end_hour_var = None
end_minute_var = None
overnight_var = None
clock_label = None
app_font = None
app_done_font = None
app_input_font = None
app_timer_font = None
timer_tick_running = False
todo_name_font = None
todo_content_font = None
todo_name_done_font = None
todo_content_done_font = None
timer_hour_format = 24
win_width_var = None
win_height_var = None
show_timer_hours = True
minute_step = 5
current_analysis_date = None
analysis_view_mode = 'day'
analysis_date_lbl = None
analysis_plot_type_var = None
analysis_figure = None
analysis_canvas_widget = None
auto_refresh_todo = False
last_save_date_str = ""
focus_panel_frame = None
focus_title_var = None
current_task_var = None
focus_timer_var = None
focus_start_btn = None
focus_pause_btn = None
focus_done_btn = None
focus_mode_running = False
focus_mode_task_idx = None
focus_mode_start_time = None
focus_mode_elapsed = 0
notified_tasks = {}
break_reminder_shown = 0
editing_task_idx = None

# --- Font Setup ---
def get_scaled_font(base_font_name="TkDefaultFont", scale_factor=1.25):
    base_font = font.nametofont(base_font_name)
    base_size = base_font.actual()["size"]
    new_size = int(base_size * scale_factor)
    if new_size < 10: new_size = 10
    scaled_font = font.Font(font=base_font)
    scaled_font.configure(size=new_size)
    return scaled_font

def show_frame(frame_to_show, parent_window):
    global active_frame
    if active_frame:
        active_frame.pack_forget()
    # Content frames are packed into the parent_window
    frame_to_show.pack(in_=parent_window, side=tki.LEFT, fill=tki.BOTH, expand=True, padx=(0, 5), pady=5)
    active_frame = frame_to_show

def toggle_new_todo_form():
    """Toggles the visibility of the new/edit todo form."""
    global new_todo_form_frame, prog_bar_frame
    global editing_task_idx
    
    if new_todo_form_frame and prog_bar_frame:
        if new_todo_form_frame.winfo_ismapped():
            new_todo_form_frame.pack_forget()
            editing_task_idx = None 
        else:
            if editing_task_idx is None:
                clear_todo_form()
            new_todo_form_frame.pack(side=tki.TOP, fill=tki.X, padx=5, pady=(5, 10), before=prog_bar_frame)

def clear_todo_form():
    """Clears all input fields in the new/edit todo form."""
    if task_name_var: task_name_var.set("")
    if task_content_text: task_content_text.delete("1.0", tki.END)
    if start_hour_var: start_hour_var.set("")
    if start_minute_var: start_minute_var.set("")
    if end_hour_var: end_hour_var.set("")
    if end_minute_var: end_minute_var.set("")
    if overnight_var: overnight_var.set(False)

def confirm_add_todo():
    global tasks, editing_task_idx
    name = task_name_var.get().strip()
    content = task_content_text.get("1.0", tki.END).strip()
    start_h = start_hour_var.get()
    start_m = start_minute_var.get()
    end_h = end_hour_var.get()
    end_m = end_minute_var.get()
    is_overnight = overnight_var.get() if overnight_var else False

    if not name:
        return  

    start_time_str = f"{start_h}:{start_m}" if start_h and start_m else None
    end_time_str = f"{end_h}:{end_m}" if end_h and end_m else None

    updated_task_data = {
        "name": name,
        "content": content,
        "start_time": start_time_str,
        "end_time": end_time_str,
        "overnight": is_overnight
    }

    if editing_task_idx is not None:
        try:
            original_task = tasks[editing_task_idx]
            updated_task_data["status"] = original_task.get("status", "pending")
            updated_task_data["completion_date"] = original_task.get("completion_date")
            tasks[editing_task_idx] = updated_task_data
        except IndexError:
            pass  
        finally:
            editing_task_idx = None 
    else:
        updated_task_data["status"] = "pending"
        updated_task_data["completion_date"] = None
        tasks.append(updated_task_data)
        
    refresh_disp()
    toggle_new_todo_form()
    sv_dat(DATA_FILE)

def cancel_add_todo():
    """Cancels the add/edit operation and hides the form."""
    global editing_task_idx
    toggle_new_todo_form()
    editing_task_idx = None

def flip_stat(idx):
    global tasks
    try:
        task = tasks[idx]
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        if task['status'] == 'pending':
            task['status'] = 'done'
            task['completion_date'] = today_str 
        else:
            task['status'] = 'pending'
            task['completion_date'] = None 
        refresh_disp()
        sv_dat(DATA_FILE)
    except IndexError:
        pass  

def del_prep(idx, action_frame):
    """Prepares for task deletion by showing confirm/cancel buttons."""
    global confirm_widgets_map
    original_del_btn = None
    for widget in action_frame.winfo_children():
        if isinstance(widget, ttk.Button) and widget.cget("text") == "Delete":
            widget.grid_forget() 
            original_del_btn = widget
            break
    else:
        return 
    confirm_btn = ttk.Button(action_frame, text="Confirm X", command=lambda i=idx: del_conf(i)) # Create confirm/cancel buttons
    cancel_btn = ttk.Button(action_frame, text="Cancel X", command=lambda af=action_frame, odb=original_del_btn: del_cancel(af, odb))
    confirm_widgets_map[action_frame] = (confirm_btn, cancel_btn, original_del_btn)
    confirm_btn.grid(row=0, column=1, pady=(0, 2), sticky=tki.EW)
    cancel_btn.grid(row=1, column=1, sticky=tki.EW)

def del_conf(idx):
    """Confirms and performs the deletion of the task at the given index."""
    global tasks, confirm_widgets_map
    try:
        tasks.pop(idx)
        refresh_disp()
        sv_dat(DATA_FILE)
    except IndexError:
        pass  

def del_cancel(action_frame, original_del_btn):
    """Cancels the delete confirmation and restores the original delete button."""
    global confirm_widgets_map
    if action_frame in confirm_widgets_map:
        confirm_btn, cancel_btn, _ = confirm_widgets_map.pop(action_frame)
        confirm_btn.destroy()
        cancel_btn.destroy()
        if original_del_btn:
             original_del_btn.grid(row=0, column=1, rowspan=2, sticky=tki.NS)

def parse_hhmm(time_str):
    if not time_str or ':' not in time_str:
        return float('inf')
    try:
        h, m = map(int, time_str.split(':'))
        if 0 <= h < 24 and 0 <= m < 60:
            return h * 60 + m
        else:
            return float('inf') 
    except ValueError:
        return float('inf') 

def refresh_disp():
    global todo_list_display_frame, done_list_display_frame, tasks, confirm_widgets_map
    global app_font, app_done_font
    global prog_lbl, prog_bar

    if not todo_list_display_frame or not done_list_display_frame or not app_font:
        return 
    confirm_widgets_map.clear()
    for widget in todo_list_display_frame.winfo_children():
        widget.destroy()
    for widget in done_list_display_frame.winfo_children():
        widget.destroy()
    pending_count = 0
    done_count = 0

    pending_tasks_with_indices = []
    done_tasks_with_indices = []

    for i, task in enumerate(tasks):
        task_tuple = (i, task)
        if task.get('status') == 'done':
            done_tasks_with_indices.append(task_tuple)
        else:
            pending_tasks_with_indices.append(task_tuple)
            
    pending_tasks_with_indices.sort(key=lambda item: parse_hhmm(item[1].get('start_time')))
    display_list = pending_tasks_with_indices + done_tasks_with_indices

    for original_idx, task in display_list:
        is_done = task.get('status') == 'done'
        parent_frame = done_list_display_frame if is_done else todo_list_display_frame

        task_block = ttk.Frame(parent_frame, padding=5)

        check_var = tki.BooleanVar(value=is_done) 
        check_btn = ttk.Checkbutton(task_block,
                                    variable=check_var,
                                    command=lambda i=original_idx: flip_stat(i))

        check_btn.pack(side=tki.LEFT, padx=(0, 10))

        action_frame = ttk.Frame(task_block)
        action_frame.columnconfigure(0, weight=0) 
        action_frame.columnconfigure(1, weight=0) 
        
        del_btn = ttk.Button(action_frame, text="Delete", width=6, command=lambda i=original_idx, af=action_frame: del_prep(i, af)) 
        del_btn.grid(row=0, column=1, rowspan=2, sticky=tki.NS) 
        edit_btn = ttk.Button(action_frame, text="Edit", width=5, command=lambda i=original_idx: start_edit_todo(i))
        edit_btn.grid(row=0, column=0, rowspan=2, sticky=tki.NS, padx=(0, 5)) 
        action_frame.pack(side=tki.RIGHT, anchor=tki.N, padx=(10, 0))
        
        details_frame = ttk.Frame(task_block)
        current_name_font = todo_name_done_font if is_done else todo_name_font
        current_content_font = todo_content_done_font if is_done else todo_content_font
        current_time_font = app_done_font if is_done else app_font

        start_t = task.get('start_time')
        end_t = task.get('end_time')
        time_str = ""
        if start_t and end_t:
            time_str = f"{start_t} ~ {end_t}"
        elif start_t:
            time_str = f"Starts: {start_t}"  
        elif end_t:
            time_str = f"Ends: {end_t}"     
        if time_str:
            time_label = ttk.Label(details_frame, text=time_str, font=current_time_font)
            time_label.pack(side=tki.RIGHT, anchor=tki.NE, padx=(10,0))

        name_label = ttk.Label(details_frame, text=task['name'], font=current_name_font)
        name_label.pack(side=tki.TOP, anchor=tki.W)

        if task.get('content'):
            content_label = ttk.Label(details_frame, text=task['content'],
                                      wraplength=400, justify=tki.LEFT, font=current_content_font)

            content_label.pack(side=tki.TOP, anchor=tki.W, pady=(0, 2), padx=(20, 0))

        details_frame.pack(side=tki.LEFT, fill=tki.BOTH, expand=True)
        task_block.pack(fill=tki.X, pady=(0, 5)) 
        ttk.Separator(parent_frame, orient='horizontal').pack(fill='x')

        if is_done:
            done_count += 1
        else:
            pending_count += 1

    if pending_count == 0:
        ttk.Label(todo_list_display_frame, text="No pending tasks!", font=app_font).pack(pady=10)
    if done_count == 0:
        ttk.Label(done_list_display_frame, text="No completed tasks yet.", font=app_font).pack(pady=10)

    if prog_lbl and prog_bar:
        total_tasks = pending_count + done_count
        if total_tasks > 0:
            completion_percent = (done_count / total_tasks) * 100
            prog_lbl.config(text=f"{done_count} / {total_tasks} tasks completed")
            prog_bar['value'] = completion_percent
        else:
            prog_lbl.config(text="No tasks yet")
            prog_bar['value'] = 0

def fmt_time(seconds):
    """Formats time values for display, supporting both clock and timer modes.When seconds="clock", formats current time based on hour format setting.Otherwise, formats the given seconds into HH:MM:SS or MM:SS based on settings."""
    global timer_hour_format, show_timer_hours
    
    if isinstance(seconds, str) and seconds == "clock":
        now = time.localtime()
        if timer_hour_format == 12:
            return time.strftime("%I:%M:%S %p", now)
        else:
            return time.strftime("%H:%M:%S", now)
    
    seconds_int = int(seconds)
    hours = seconds_int // 3600
    minutes = (seconds_int % 3600) // 60
    secs = seconds_int % 60
    
    if show_timer_hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        total_minutes = (seconds_int // 60)
        return f"{total_minutes:02d}:{secs:02d}"

def upd_clk():
    """Updates the clock display every second."""
    global clock_label
    if clock_label:
        time_string = fmt_time("clock")
        clock_label.config(text=time_string)
        clock_label.after(1000, upd_clk)

def upd_tmr_dsp():
    """Updates all timer displays with current elapsed time values."""
    global timers, app_timer_font
    for tmr_data in timers:
        if 'time_label' in tmr_data['widgets']:
            display_time = tmr_data['elapsed']
            if tmr_data['running'] and tmr_data['start_time']:
                display_time += time.time() - tmr_data['start_time']
            tmr_data['widgets']['time_label'].config(text=fmt_time(display_time))

def tick_tmrs():
    """Updates running timers every second and schedules the next update."""
    global timers, timer_tick_running
    any_running = False
    for tmr_data in timers:
        if tmr_data['running'] and tmr_data['enabled']:
            any_running = True
            break

    if any_running:
        upd_tmr_dsp()
        timer_tick_running = True
        if clock_label:
             clock_label.after(1000, tick_tmrs)
        else:
            timer_tick_running = False
    else:
        timer_tick_running = False

def maybe_start_ticker():
    """Starts the timer update loop if not already running."""
    global timer_tick_running
    if not timer_tick_running:
        tick_tmrs()

def strt_tmr(tmr_id):
    """Starts the specified timer and pauses any other running timers."""
    global timers
    
    for i, t in enumerate(timers):
        if t['id'] != tmr_id and t['running'] and t['enabled']:
            pse_tmr(t['id'])

    for tmr_data in timers:
        if tmr_data['id'] == tmr_id and tmr_data['enabled']:
            if not tmr_data['running']:
                tmr_data['running'] = True
                tmr_data['start_time'] = time.time()
                
                if 'start_btn' in tmr_data['widgets']:
                    tmr_data['widgets']['start_btn'].config(state=tki.DISABLED)
                if 'pause_btn' in tmr_data['widgets']:
                    tmr_data['widgets']['pause_btn'].config(state=tki.NORMAL)
                maybe_start_ticker()
            break

def pse_tmr(tmr_id):
    """Pauses the specified timer and saves its elapsed time."""
    global timers
    timer_was_running = False
    for tmr_data in timers:
        if tmr_data['id'] == tmr_id and tmr_data['enabled']:
            if tmr_data['running']:
                timer_was_running = True
                tmr_data['running'] = False
                
                if tmr_data['start_time']:
                     tmr_data['elapsed'] += time.time() - tmr_data['start_time']
                tmr_data['start_time'] = None
                upd_tmr_dsp()
                
                if 'start_btn' in tmr_data['widgets']:
                    tmr_data['widgets']['start_btn'].config(state=tki.NORMAL)
                if 'pause_btn' in tmr_data['widgets']:
                    tmr_data['widgets']['pause_btn'].config(state=tki.DISABLED)
            break
            
    if timer_was_running:
        sv_dat(DATA_FILE)

def rst_tmr(tmr_id):
    """Resets the specified timer to zero."""
    global timers
    for tmr_data in timers:
        if tmr_data['id'] == tmr_id:
            tmr_data['running'] = False
            tmr_data['elapsed'] = 0
            tmr_data['start_time'] = None
            upd_tmr_dsp()
            
            if tmr_data['enabled']:
                 if 'start_btn' in tmr_data['widgets']:
                    tmr_data['widgets']['start_btn'].config(state=tki.NORMAL)
                 if 'pause_btn' in tmr_data['widgets']:
                    tmr_data['widgets']['pause_btn'].config(state=tki.DISABLED)
            else:
                 if 'start_btn' in tmr_data['widgets']:
                    tmr_data['widgets']['start_btn'].config(state=tki.DISABLED)
                 if 'pause_btn' in tmr_data['widgets']:
                    tmr_data['widgets']['pause_btn'].config(state=tki.DISABLED)
            break

def tog_ena(tmr_id):
    """Toggles a timer's enabled state and updates UI accordingly."""
    global timers
    
    for tmr_data in timers:
         if tmr_data['id'] == tmr_id:
            tmr_data['enabled'] = not tmr_data['enabled']
            
            if not tmr_data['enabled'] and tmr_data['running']:
                pse_tmr(tmr_id)
                
            is_enabled = tmr_data['enabled']
            start_state = tki.NORMAL if is_enabled else tki.DISABLED
            pause_state = tki.DISABLED

            if 'start_btn' in tmr_data['widgets']:
                tmr_data['widgets']['start_btn'].config(state=start_state)
            if 'pause_btn' in tmr_data['widgets']:
                tmr_data['widgets']['pause_btn'].config(state=pause_state)
            break
            
    upd_tmr_dsp()

def crt_tmr_blk(parent, tmr_data):
    """Creates a timer block UI component for the given timer data."""
    global app_font, app_timer_font
    tmr_id = tmr_data['id']
    is_enabled = tmr_data['enabled']

    block_frame = ttk.Frame(parent, borderwidth=1, relief=tki.GROOVE, padding=10)

    enable_var = tki.BooleanVar(value=is_enabled)
    enable_check = ttk.Checkbutton(block_frame, variable=enable_var,
                                     command=lambda i=tmr_id: tog_ena(i))
    enable_check.pack(side=tki.LEFT, anchor=tki.N, padx=(0, 5))

    content_frame = ttk.Frame(block_frame)
    content_frame.pack(side=tki.LEFT, fill=tki.BOTH, expand=True)

    name_label = ttk.Label(content_frame, text=tmr_data['name'], font=app_font)
    name_label.pack(pady=(0, 5))
    tmr_data['widgets']['name_label'] = name_label

    time_label = ttk.Label(content_frame, text=fmt_time(tmr_data['elapsed']), font=app_timer_font)
    time_label.pack(pady=(0, 10))
    tmr_data['widgets']['time_label'] = time_label

    button_frame = ttk.Frame(content_frame)
    button_frame.pack(pady=(5, 0))

    start_state = tki.NORMAL if is_enabled else tki.DISABLED
    pause_state = tki.DISABLED
    fixed_button_width = 8

    start_btn = ttk.Button(button_frame, text="Start", state=start_state,
                           width=fixed_button_width,
                           command=lambda i=tmr_id: strt_tmr(i))
    start_btn.pack(side=tki.TOP, pady=4, anchor=tki.CENTER) 
    tmr_data['widgets']['start_btn'] = start_btn

    pause_btn = ttk.Button(button_frame, text="Pause", state=pause_state,
                           width=fixed_button_width,
                           command=lambda i=tmr_id: pse_tmr(i))
    pause_btn.pack(side=tki.TOP, pady=4, anchor=tki.CENTER) 
    tmr_data['widgets']['pause_btn'] = pause_btn

    reset_btn = ttk.Button(button_frame, text="Reset",
                           width=fixed_button_width,
                           command=lambda i=tmr_id: rst_tmr(i))
    reset_btn.pack(side=tki.TOP, pady=4, anchor=tki.CENTER) 
    tmr_data['widgets']['reset_btn'] = reset_btn

    return block_frame

def main():
    global new_todo_form_frame, todo_list_display_frame, done_list_display_frame
    global task_name_var, task_content_text, start_hour_var, start_minute_var, end_hour_var, end_minute_var
    global app_font, app_done_font, app_input_font, app_timer_font, clock_label
    global timers, win_width_var, win_height_var 
    global prog_bar_frame, prog_lbl, prog_bar
    global current_analysis_date 
    # Make Matplotlib globals accessible
    global analysis_date_lbl, analysis_plot_type_var, analysis_figure, analysis_canvas_widget, analysis_content_frm
    global pending_canvas, done_canvas 
    global end_hour_combo, end_minute_combo 
    global overnight_var 
    global focus_panel_frame, focus_title_var, current_task_var, focus_timer_var
    global focus_start_btn, focus_pause_btn, focus_done_btn
    global focus_mode_running, focus_mode_task_idx, focus_mode_start_time, focus_mode_elapsed
    global window 
    global notified_tasks, break_reminder_shown
    global editing_task_idx
    # --- Initialize Window, Fonts, TTK UI style, Setting and variables---
    window = tki.Tk()
    window.title("FocusFlow App")
    window.geometry("800x800") 
    ld_dat(DATA_FILE)
    app_font = get_scaled_font()
    app_input_font = get_scaled_font()
    app_timer_font = get_scaled_font(scale_factor=1.8)
    app_done_font = font.Font(font=app_font)
    app_done_font.configure(overstrike=True)
    base_todo_size = app_font.actual()['size']
    todo_name_size = int(base_todo_size * 1.1) 
    todo_content_size = int(base_todo_size * 0.85) 

    if todo_content_size < 9: todo_content_size = 9 
    global todo_name_font, todo_content_font, todo_name_done_font, todo_content_done_font

    todo_name_font = font.Font(font=app_font)
    todo_name_font.configure(size=todo_name_size)
    todo_content_font = font.Font(font=app_font)
    todo_content_font.configure(size=todo_content_size)
    todo_name_done_font = font.Font(font=todo_name_font)
    todo_name_done_font.configure(overstrike=True)
    todo_content_done_font = font.Font(font=todo_content_font)
    todo_content_done_font.configure(overstrike=True)

    style = ttk.Style()
    style.configure('.', font=app_font)
    style.configure('TButton', font=app_font)
    style.configure('TLabel', font=app_font)
    style.configure('TEntry', font=app_input_font)
    style.configure('TCombobox', font=app_input_font)
    style.configure('TCheckbutton', font=app_font)
    style.configure('Clock.TLabel', font=app_timer_font, padding=(10, 5))
    style.configure('Nav.TButton', font=app_font)

    task_name_var = tki.StringVar()
    start_hour_var = tki.StringVar()
    start_minute_var = tki.StringVar()
    end_hour_var = tki.StringVar()
    end_minute_var = tki.StringVar()

    win_width_var = tki.StringVar(value="800") 
    win_height_var = tki.StringVar(value="800") 
    time_format_var = tki.StringVar(value="24-Hour") 
    analysis_plot_type_var = tki.StringVar()
    
    global timer_hour_format, show_timer_hours
    timer_hour_format = 24  
    hours_list = [f"{h:02d}" for h in range(24)]
    
    # Use minute_step to generate minutes list
    minutes_list = []
    for m in range(0, 60, minute_step):
        minutes_list.append(f"{m:02d}")

    # --- Navigation Frame --- 
    nav_frame = ttk.Frame(window, width=180) 
    nav_frame.pack(side=tki.LEFT, fill=tki.Y, padx=(5, 0), pady=5)
    nav_frame.pack_propagate(False)

    # --- Separator ---
    separator = ttk.Separator(window, orient='vertical')
    separator.pack(side=tki.LEFT, fill='y', padx=5)

    content_base_frame = ttk.Frame(window)

    # --- ToDo Frame Setup (Inside content_base_frame) ---
    todo_frame = ttk.Frame(content_base_frame)
    new_todo_button_frame = ttk.Frame(todo_frame)
    add_todo_btn = ttk.Button(new_todo_button_frame, text="+ New ToDo", command=toggle_new_todo_form)
    add_todo_btn.pack(side=tki.LEFT, pady=5)
    focus_btn = ttk.Button(new_todo_button_frame, text="Focus Mode", command=toggle_focus_mode)
    focus_btn.pack(side=tki.RIGHT, pady=5)
    new_todo_button_frame.pack(side=tki.TOP, fill=tki.X, anchor=tki.NW, padx=5)
    focus_panel_frame = ttk.Frame(todo_frame, relief=tki.GROOVE, borderwidth=1, padding=10)
    focus_title_var = tki.StringVar(value="Focus Mode")
    focus_title = ttk.Label(focus_panel_frame, textvariable=focus_title_var, 
                           font=get_scaled_font(scale_factor=1.3))
    focus_title.pack(pady=(0, 10))
    
    # Current task&Focus Time display
    current_task_var = tki.StringVar(value="No current task")
    current_task_lbl = ttk.Label(focus_panel_frame, textvariable=current_task_var,
                                font=get_scaled_font(scale_factor=1.2))
    current_task_lbl.pack(pady=5)
    focus_timer_var = tki.StringVar(value="00:00:00")
    focus_timer_lbl = ttk.Label(focus_panel_frame, textvariable=focus_timer_var,
                               font=get_scaled_font(scale_factor=1.5))
    focus_timer_lbl.pack(pady=5)
    
    focus_controls_frame = ttk.Frame(focus_panel_frame)
    focus_controls_frame.pack(pady=10)
    focus_start_btn = ttk.Button(focus_controls_frame, text="Start", command=start_focus_timer)
    focus_start_btn.pack(side=tki.LEFT, padx=5)
    focus_pause_btn = ttk.Button(focus_controls_frame, text="Pause", command=pause_focus_timer, state=tki.DISABLED)
    focus_pause_btn.pack(side=tki.LEFT, padx=5)
    focus_done_btn = ttk.Button(focus_controls_frame, text="Mark Done", command=mark_focus_task_done)
    focus_done_btn.pack(side=tki.LEFT, padx=5)
    
    # --- Progress Bar Area ---
    global prog_bar_frame, prog_lbl, prog_bar 
    prog_bar_frame = ttk.Frame(todo_frame, padding=(0, 5, 0, 10))
    prog_lbl = ttk.Label(prog_bar_frame, text="Calculating progress...", anchor=tki.CENTER)
    prog_lbl.pack(fill=tki.X)
    prog_bar = ttk.Progressbar(prog_bar_frame, orient=tki.HORIZONTAL, length=200, mode='determinate')
    prog_bar.pack(fill=tki.X, pady=(2,0))
    prog_bar_frame.pack(side=tki.TOP, fill=tki.X, padx=5, pady=(5, 0)) 

    new_todo_form_frame = ttk.Frame(todo_frame, relief=tki.GROOVE, borderwidth=1, padding=10)
    new_todo_form_frame.columnconfigure(1, weight=1) 
    new_todo_form_frame.columnconfigure(2, weight=1) 
    new_todo_form_frame.columnconfigure(3, weight=0) 
    
    name_label = ttk.Label(new_todo_form_frame, text="Name:")
    name_label.grid(row=0, column=0, sticky=tki.W, padx=5, pady=2)
    name_entry = ttk.Entry(new_todo_form_frame, textvariable=task_name_var, font=app_input_font) 
    name_entry.grid(row=0, column=1, columnspan=3, sticky=tki.EW, padx=5, pady=2) 
    
    start_time_label = ttk.Label(new_todo_form_frame, text="Start Time (HH:MM):")
    start_time_label.grid(row=1, column=0, sticky=tki.W, padx=5, pady=2)
    
    start_hour_combo = ttk.Combobox(new_todo_form_frame, textvariable=start_hour_var, values=hours_list, width=4)
    start_hour_combo.grid(row=1, column=1, sticky=tki.W, padx=(5,0), pady=2)
    start_hour_combo.bind("<<ComboboxSelected>>", upd_end_hrs) # Bind the update function
    start_minute_combo = ttk.Combobox(new_todo_form_frame, textvariable=start_minute_var, values=minutes_list, width=4)
    start_minute_combo.grid(row=1, column=2, sticky=tki.W, padx=(0,5), pady=2)
    start_minute_combo.bind("<<ComboboxSelected>>", upd_end_mins)
    
    end_time_label = ttk.Label(new_todo_form_frame, text="End Time (HH:MM):")
    end_time_label.grid(row=2, column=0, sticky=tki.W, padx=5, pady=2)
    end_hour_combo_widget = ttk.Combobox(new_todo_form_frame, textvariable=end_hour_var, values=hours_list, width=4)
    end_hour_combo_widget.grid(row=2, column=1, sticky=tki.W, padx=(5,0), pady=2)
    end_hour_combo = end_hour_combo_widget 
    end_hour_combo.bind("<<ComboboxSelected>>", upd_end_mins)  
    
    end_minute_combo_widget = ttk.Combobox(new_todo_form_frame, textvariable=end_minute_var, values=minutes_list, width=4)
    end_minute_combo_widget.grid(row=2, column=2, sticky=tki.W, padx=(0,5), pady=2)
    end_minute_combo = end_minute_combo_widget #：(

    overnight_var = tki.BooleanVar(value=False)
    overnight_check = ttk.Checkbutton(new_todo_form_frame, text="Overnight", 
                                      variable=overnight_var, command=upd_end_hrs)
    overnight_check.grid(row=2, column=3, sticky=tki.W, padx=(10, 0), pady=2)
    
    content_label = ttk.Label(new_todo_form_frame, text="Content/Notes:")
    content_label.grid(row=3, column=0, sticky=tki.NW, padx=5, pady=2)
    task_content_text = tki.Text(new_todo_form_frame, height=4, font=app_input_font) 
    task_content_text.grid(row=3, column=1, columnspan=3, sticky=tki.EW, padx=5, pady=2) 
    
    form_buttons_frame = ttk.Frame(new_todo_form_frame)
    confirm_btn = ttk.Button(form_buttons_frame, text="Confirm", command=confirm_add_todo)
    confirm_btn.pack(side=tki.LEFT, padx=5)
    cancel_btn = ttk.Button(form_buttons_frame, text="Cancel", command=cancel_add_todo)
    cancel_btn.pack(side=tki.LEFT, padx=5)
    form_buttons_frame.grid(row=4, column=1, columnspan=3, sticky=tki.E, pady=5)

    global pending_area_frame 

    pending_area_frame = ttk.Frame(todo_frame)
    pending_canvas = tki.Canvas(pending_area_frame, borderwidth=0, highlightthickness=0)
    pending_scrollbar = ttk.Scrollbar(pending_area_frame, orient="vertical", command=pending_canvas.yview)
    todo_list_display_frame = ttk.Frame(pending_canvas) 
    
    pending_canvas_window = pending_canvas.create_window((0, 0), window=todo_list_display_frame, anchor="nw")
    
    # Define the configure callback for the pending canvas
    def configure_pending_canvas(event):
        pending_canvas.configure(scrollregion=pending_canvas.bbox("all"))
        pending_canvas.itemconfig(pending_canvas_window, width=event.width)
        
    pending_canvas.bind("<Configure>", configure_pending_canvas)
    pending_canvas.configure(yscrollcommand=pending_scrollbar.set)
    
    # Bug Fixed by AI（Gemini）,but it still exist.... Added mouse wheel scroll event binding and Scroll bar conflict, This was a huge problem I encountered :(
    def wheel_scroll(event, canvas):
        if event.delta:
            # For Windows
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:
            # For Linux - scroll up
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            # For Linux - scroll down
            canvas.yview_scroll(1, "units")
        return "break"  # Prevent the event from propagating
        
    pending_canvas.bind("<MouseWheel>", lambda event: wheel_scroll(event, pending_canvas))  # Windows
    pending_canvas.bind("<Button-4>", lambda event: wheel_scroll(event, pending_canvas))    # Linux scroll up
    pending_canvas.bind("<Button-5>", lambda event: wheel_scroll(event, pending_canvas))    # Linux scroll down
    
    pending_canvas.pack(side=tki.LEFT, fill=tki.BOTH, expand=True)
    pending_scrollbar.pack(side=tki.RIGHT, fill=tki.Y)
    pending_area_frame.pack(side=tki.TOP, fill=tki.BOTH, expand=True, padx=5, pady=(0, 10))

    list_separator = ttk.Separator(todo_frame, orient='horizontal')
    list_separator.pack(side=tki.TOP, fill='x', padx=5, pady=5)

    # --- Done Tasks Area with Scrollbar ---
    done_area_frame = ttk.Frame(todo_frame)
    done_canvas = tki.Canvas(done_area_frame, borderwidth=0, highlightthickness=0)
    done_scrollbar = ttk.Scrollbar(done_area_frame, orient="vertical", command=done_canvas.yview)
    done_list_display_frame = ttk.Frame(done_canvas) 
    
    done_canvas_window = done_canvas.create_window((0, 0), window=done_list_display_frame, anchor="nw")
    
    def configure_done_canvas(event):
        done_canvas.configure(scrollregion=done_canvas.bbox("all"))
        done_canvas.itemconfig(done_canvas_window, width=event.width)
        
    done_canvas.bind("<Configure>", configure_done_canvas) # done_list_display_frame.unbind("<Configure>")

    done_canvas.configure(yscrollcommand=done_scrollbar.set)
    done_canvas.pack(side=tki.LEFT, fill=tki.BOTH, expand=True)
    done_scrollbar.pack(side=tki.RIGHT, fill=tki.Y)
    done_area_frame.pack(side=tki.TOP, fill=tki.BOTH, expand=True, padx=5, pady=(0, 5))
    
    todo_frame.pack(fill=tki.BOTH, expand=True)

    # --- Timer Frame Setup (Inside content_base_frame) ---
    timer_frame = ttk.Frame(content_base_frame)
    clock_frame = ttk.Frame(timer_frame)
    clock_label = ttk.Label(clock_frame, text="--:--:--", style='Clock.TLabel')
    clock_label.pack()
    clock_frame.pack(side=tki.TOP, fill=tki.X, pady=10)
    
    timers_grid_frame = ttk.Frame(timer_frame)
    timers_grid_frame.pack(side=tki.TOP, fill=tki.BOTH, expand=True, padx=10, pady=10)
    timers_grid_frame.columnconfigure(0, weight=1)
    timers_grid_frame.columnconfigure(1, weight=1)
    timers_grid_frame.rowconfigure(0, weight=1)
    timers_grid_frame.rowconfigure(1, weight=1)
    timer_block_positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    
    for i, tmr_data in enumerate(timers):
        row, col = timer_block_positions[i]
        timer_block = crt_tmr_blk(timers_grid_frame, tmr_data)
        timer_block.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    # --- Analysis Frame Setup (Enhanced with Plotting) ---
    analysis_frame = ttk.Frame(content_base_frame, padding=10)
    
    # Top Navigation Bar for Analysis+Pack right&Left-aligned button
    analysis_nav_frm = ttk.Frame(analysis_frame)
    analysis_nav_frm.pack(side=tki.TOP, fill=tki.X, pady=(0, 10))
    
    view_toggle_btn = ttk.Button(analysis_nav_frm, text="View: Day", width=10, command=toggle_analysis_view)
    view_toggle_btn.pack(side=tki.RIGHT, padx=(10, 0))
    prev_btn = ttk.Button(analysis_nav_frm, text="<", width=3, command=lambda: change_analysis_date(-1))
    prev_btn.pack(side=tki.LEFT, padx=(0, 5))
    
    analysis_date_lbl = ttk.Label(analysis_nav_frm, text="-", width=25, anchor=tki.CENTER, font=app_font)
    analysis_date_lbl.pack(side=tki.LEFT, expand=True, fill=tki.X, padx=5) # Allow label to expand
    
    next_btn = ttk.Button(analysis_nav_frm, text=">", width=3, command=lambda: change_analysis_date(1))
    next_btn.pack(side=tki.LEFT, padx=5)
    
    plot_options = [
        "Work/Study Time",
        "Rest/Entertain Time",
        "Sleep/Eat Time",
        "Others Time",
        "Tasks Completed"
    ]
    analysis_plot_type_combo = ttk.Combobox(analysis_nav_frm, textvariable=analysis_plot_type_var,
                                           values=plot_options, state="readonly", width=20)
    analysis_plot_type_combo.pack(side=tki.LEFT, padx=5)
    analysis_plot_type_combo.set(plot_options[0]) 
    analysis_plot_type_combo.bind("<<ComboboxSelected>>", lambda e: update_analysis_display()) # Update plot on selection change

    analysis_content_frm = ttk.Frame(analysis_frame, relief=tki.GROOVE, borderwidth=1)
    analysis_content_frm.pack(side=tki.TOP, fill=tki.BOTH, expand=True, pady=(10, 0))

    # Solve by Gemini in about L850-950
    # Initialize Matplotlib Figure and Canvas(The Requirement conflict and errors, canvas/frame bugs Solved by Gemini)
    if matplotlib_available:
        analysis_figure = Figure(figsize=(6, 4), dpi=100) # Initial size
        # Prevent Tkinter from shrinking the plot area if window is small
        analysis_content_frm.pack_propagate(False)
        analysis_canvas_widget = FigureCanvasTkAgg(analysis_figure, master=analysis_content_frm)
        analysis_canvas_widget_tk = analysis_canvas_widget.get_tk_widget()
        analysis_canvas_widget_tk.pack(side=tki.TOP, fill=tki.BOTH, expand=True)
    else:
        # Display a message if matplotlib is not available
        fallback_lbl = ttk.Label(analysis_content_frm, text="Matplotlib not found. Plotting disabled.", anchor=tki.CENTER)
        fallback_lbl.pack(pady=20)

    # --- Settings Frame Setup (Modernized Layout) ---
    settings_frame = ttk.Frame(content_base_frame, padding=20)
    settings_inner_container = ttk.Frame(settings_frame) # Main vertical container
    settings_inner_container.pack(fill=tki.X)

    # --- User Name Setting ---
    user_name_frm = ttk.Frame(settings_inner_container, padding=(0, 5, 0, 5))
    ttk.Label(user_name_frm, text="Your Name", width=15, anchor=tki.W).pack(side=tki.LEFT, padx=(0, 15))
    
    user_name_controls_frm = ttk.Frame(user_name_frm)
    user_name_var = tki.StringVar(value=user_name)  
    user_name_entry = ttk.Entry(user_name_controls_frm, textvariable=user_name_var, width=20, font=app_input_font)
    user_name_entry.pack(side=tki.LEFT, padx=(0, 10))
    save_name_btn = ttk.Button(user_name_controls_frm, text="Apply", 
                              command=lambda: set_user_name(user_name_var.get()))
    save_name_btn.pack(side=tki.LEFT)
    user_name_controls_frm.pack(side=tki.LEFT)
    user_name_frm.pack(fill=tki.X, pady=(0, 10))
    ttk.Separator(settings_inner_container, orient='horizontal').pack(fill='x', pady=(5, 15))
    
    # --- Window Size Setting ---
    win_sz_frm = ttk.Frame(settings_inner_container, padding=(0, 5, 0, 5))
    ttk.Label(win_sz_frm, text="Window Size", width=15, anchor=tki.W).pack(side=tki.LEFT, padx=(0, 15))
    win_sz_controls_frm = ttk.Frame(win_sz_frm)
    ttk.Label(win_sz_controls_frm, text="Width:").pack(side=tki.LEFT, padx=(0, 2))
    width_entry = ttk.Entry(win_sz_controls_frm, textvariable=win_width_var, width=6, font=app_input_font)
    width_entry.pack(side=tki.LEFT, padx=(0, 10))
    ttk.Label(win_sz_controls_frm, text="Height:").pack(side=tki.LEFT, padx=(0, 2))
    height_entry = ttk.Entry(win_sz_controls_frm, textvariable=win_height_var, width=6, font=app_input_font)
    height_entry.pack(side=tki.LEFT, padx=(0, 15))
    
    apply_size_btn = ttk.Button(win_sz_controls_frm, text="Apply", command=apply_win_sz)
    apply_size_btn.pack(side=tki.LEFT)
    win_sz_controls_frm.pack(side=tki.LEFT)
    
    win_sz_frm.pack(fill=tki.X, pady=(0, 10))
    ttk.Separator(settings_inner_container, orient='horizontal').pack(fill='x', pady=(5, 15))

    # --- Clock Format Setting ---
    clk_fmt_frm = ttk.Frame(settings_inner_container, padding=(0, 5, 0, 5))
    ttk.Label(clk_fmt_frm, text="Clock Format", width=15, anchor=tki.W).pack(side=tki.LEFT, padx=(0, 15))
    
    clk_fmt_controls_frm = ttk.Frame(clk_fmt_frm)
    time_format_combo = ttk.Combobox(clk_fmt_controls_frm, textvariable=time_format_var,
                                       values=["12-Hour", "24-Hour"], state="readonly", width=10)
    time_format_combo.pack(side=tki.LEFT, padx=(0, 10))
    time_format_combo.bind("<<ComboboxSelected>>", lambda event: set_tm_fmt(time_format_var.get()))
    # Remove grey hint label
    # ttk.Label(clk_fmt_controls_frm, text="Format for the clock display at the top of the Timer tab.", foreground="grey").pack(side=tki.LEFT)
    clk_fmt_controls_frm.pack(side=tki.LEFT)
    
    clk_fmt_frm.pack(fill=tki.X, pady=(0, 10))
    ttk.Separator(settings_inner_container, orient='horizontal').pack(fill='x', pady=(5, 15))

    # --- Timer Display Settings ---
    tmr_dsp_frm = ttk.Frame(settings_inner_container, padding=(0, 5, 0, 5))
    ttk.Label(tmr_dsp_frm, text="Timer Display", width=15, anchor=tki.W).pack(side=tki.LEFT, padx=(0, 15))
    
    tmr_dsp_controls_frm = ttk.Frame(tmr_dsp_frm)
    show_hours_var = tki.BooleanVar(value=show_timer_hours)
    hours_check = ttk.Checkbutton(tmr_dsp_controls_frm, text="Show Hours (HH:MM:SS)",
                                variable=show_hours_var, command=tog_tmr_hrs)
    hours_check.pack(side=tki.LEFT, padx=(0, 10))
    # Remove grey hint label
    # ttk.Label(tmr_dsp_controls_frm, text="Display hours in individual timer blocks.", foreground="grey").pack(side=tki.LEFT)
    tmr_dsp_controls_frm.pack(side=tki.LEFT)
    
    tmr_dsp_frm.pack(fill=tki.X, pady=(0, 10))
    ttk.Separator(settings_inner_container, orient='horizontal').pack(fill='x', pady=(5, 15))
    
    # --- Minute Step Setting --- (Rename Label)
    min_stp_frm = ttk.Frame(settings_inner_container, padding=(0, 5, 0, 5))
    ttk.Label(min_stp_frm, text="New/Edit Todos Minute step", width=25, anchor=tki.W).pack(side=tki.LEFT, padx=(0, 15)) # Rename Label

    min_stp_controls_frm = ttk.Frame(min_stp_frm)
    step_options = [1, 2, 3, 5, 10, 15, 20, 30]
    step_var = tki.StringVar(value=str(minute_step))
    step_combo = ttk.Combobox(min_stp_controls_frm, textvariable=step_var, values=step_options,
                            width=5, state="readonly")
    step_combo.pack(side=tki.LEFT, padx=(0, 10))
    step_combo.bind("<<ComboboxSelected>>", lambda event: set_min_step(int(step_var.get())))
    # Remove grey hint label
    # ttk.Label(min_stp_controls_frm, text="Minute interval for time dropdowns in new ToDo form.", foreground="grey").pack(side=tki.LEFT)
    min_stp_controls_frm.pack(side=tki.LEFT)
    min_stp_frm.pack(fill=tki.X, pady=(0, 10))
    ttk.Separator(settings_inner_container, orient='horizontal').pack(fill='x', pady=(5, 15))

    # --- Auto Refresh Setting ---
    auto_ref_frm = ttk.Frame(settings_inner_container, padding=(0, 5, 0, 5))
    ttk.Label(auto_ref_frm, text="Daily Refresh", width=15, anchor=tki.W).pack(side=tki.LEFT, padx=(0, 15))
    
    auto_ref_controls_frm = ttk.Frame(auto_ref_frm)
    auto_refresh_var = tki.BooleanVar(value=auto_refresh_todo) # Use loaded value
    auto_ref_check = ttk.Checkbutton(auto_ref_controls_frm, text="Clear all ToDos at midnight",
                                     variable=auto_refresh_var, command=tog_auto_ref)
    auto_ref_check.pack(side=tki.LEFT, padx=(0, 10))
    auto_ref_controls_frm.pack(side=tki.LEFT)
    
    auto_ref_frm.pack(fill=tki.X, pady=(5, 10)) # Adjusted padding slightly 

    content_base_frame.pack(side=tki.LEFT, fill=tki.BOTH, expand=True, padx=(0, 5), pady=5)

    # --- Create specific font for Nav Buttons ---
    nav_button_font = font.Font(font=app_font)
    nav_button_base_size = nav_button_font.actual()["size"]
    nav_button_font.configure(size=int(nav_button_base_size * 1.25))

    outer_pady = 15 
    inner_ipady = 5 
    todo_btn = ttk.Button(nav_frame, text="Todo",
                          style='Nav.TButton', 
                          command=lambda: show_frame(todo_frame, content_base_frame))
    todo_btn.pack(pady=outer_pady, ipady=inner_ipady, padx=10, fill=tki.X) 
    
    timer_btn = ttk.Button(nav_frame, text="Timer", style='Nav.TButton', 
                           command=lambda: show_frame(timer_frame, content_base_frame))
    timer_btn.pack(pady=outer_pady, ipady=inner_ipady, padx=10, fill=tki.X) 
    
    analysis_btn = ttk.Button(nav_frame, text="Analysis", style='Nav.TButton', 
                              command=lambda: show_frame(analysis_frame, content_base_frame))
    analysis_btn.pack(pady=outer_pady, ipady=inner_ipady, padx=10, fill=tki.X) 
    
    settings_btn = ttk.Button(nav_frame, text="Settings", style='Nav.TButton',
                              command=lambda: show_frame(settings_frame, content_base_frame))
    settings_btn.pack(pady=outer_pady, ipady=inner_ipady, padx=10, fill=tki.X) 

    # --- Initial Frame Display & Start Loops ---
    show_frame(todo_frame, content_base_frame)
    refresh_disp()
    upd_clk() 
    upd_tmr_dsp() 
    maybe_start_ticker() 

    # Initialize analysis view
    current_analysis_date = datetime.date.today() 
    update_analysis_display() 

    # --- Start Notification Check Loop ---
    check_task_notifications() 
    window.protocol("WM_DELETE_WINDOW", lambda: hdl_close(window))
    window.mainloop()

# --- Settings Functions ---
def apply_win_sz():
    global win_width_var, win_height_var
    try:
        new_w = int(win_width_var.get())
        new_h = int(win_height_var.get())
        if new_w >= 600 and new_h >= 600: 
            if clock_label:
                 root = clock_label.winfo_toplevel()
                 root.geometry(f"{new_w}x{new_h}")
    except (ValueError, Exception):
        pass 

def set_tm_fmt(choice):
    global timer_hour_format
    if choice == "12-Hour":
        timer_hour_format = 12
    else:
        timer_hour_format = 24
    if clock_label:
        upd_clk()
    sv_dat(DATA_FILE)

def tog_tmr_hrs():
    global show_timer_hours
    show_timer_hours = not show_timer_hours
    upd_tmr_dsp()  # Update timer displays immediately
    sv_dat(DATA_FILE) # Save setting immediately

def set_min_step(new_step):
    global minute_step
    minute_step = new_step
    # Update the minute comboboxes in the new todo form
    new_minutes_list = [f"{m:02d}" for m in range(0, 60, minute_step)]
    
    # Update comboboxes directly if they exist
    try:
        if 'start_minute_combo' in globals() and start_minute_combo:
            start_minute_combo.config(values=new_minutes_list)
        if 'end_minute_combo' in globals() and end_minute_combo:
            end_minute_combo.config(values=new_minutes_list)
    except NameError:
        pass # Widgets might not be created yet
    
    sv_dat(DATA_FILE) # Save setting immediately

# --- Callback for Start Hour Change ---
def upd_end_hrs(*args): # Use *args to accept potential event details
    global start_hour_var, end_hour_var, end_hour_combo, overnight_var
    
    # Skip update if not initialized
    if end_hour_combo is None:
        return
    
    start_h_str = start_hour_var.get()
    current_end_h = end_hour_var.get()
    is_overnight = overnight_var.get() if overnight_var else False
    
    try:
        # If overnight is checked, allow full range of end hours
        if is_overnight:
            valid_end_hours = [f"{h:02d}" for h in range(24)]
        else:
            # Otherwise restrict end hours to be >= start hour
            start_h = int(start_h_str) if start_h_str else 0
            if not (0 <= start_h < 24):
                raise ValueError # Invalid hour range
                
            # Generate new list of end hours from start_h to 23
            valid_end_hours = [f"{h:02d}" for h in range(start_h, 24)]
        
        # Update end hour combo values
        if end_hour_combo:
            end_hour_combo.config(values=valid_end_hours)
            # If current end hour is no longer valid, set to first valid
            if current_end_h and current_end_h not in valid_end_hours:
                if valid_end_hours:
                    end_hour_var.set(valid_end_hours[0])
                else:
                    end_hour_var.set("")
        
        # Update end minute options too, in case we're in same-hour scenario
        upd_end_mins()
                
    except (ValueError, TypeError):
        # Invalid start hour or cleared, reset to full list if overnight
        if is_overnight:
            full_hours_list = [f"{h:02d}" for h in range(24)]
            if end_hour_combo:
                end_hour_combo.config(values=full_hours_list)

# --- Callback for Minute Update ---
def upd_end_mins(*args):
    global start_hour_var, start_minute_var, end_hour_var, end_minute_var, end_minute_combo, minute_step
    
    # Skip if not initialized
    if end_minute_combo is None:
        return
    
    start_h_str = start_hour_var.get()
    start_m_str = start_minute_var.get()
    end_h_str = end_hour_var.get()
    current_end_m = end_minute_var.get()
    
    try:
        # Check if both hours are same and valid
        if start_h_str and end_h_str and start_h_str == end_h_str:
            # Same hour - restrict minutes
            start_m = int(start_m_str) if start_m_str else 0
            
            # Only show minutes greater than start minute
            valid_end_minutes = []
            for m in range(0, 60, minute_step):
                if m > start_m:
                    valid_end_minutes.append(f"{m:02d}")
            
            # If no valid minutes (e.g., if start is 55 and step is 10), 
            # add the next hour's first minute
            if not valid_end_minutes:
                valid_end_minutes = ["00"]  # This case should be rare with overnight option
            
            # Update end minute combo values
            end_minute_combo.config(values=valid_end_minutes)
            
            # If current end minute is no longer valid, set to first valid
            if not current_end_m or current_end_m not in valid_end_minutes:
                if valid_end_minutes:
                    end_minute_var.set(valid_end_minutes[0])
                else:
                    end_minute_var.set("")
        else:
            # Different hours - restore full minute options
            full_minutes_list = [f"{m:02d}" for m in range(0, 60, minute_step)]
            end_minute_combo.config(values=full_minutes_list)
            
    except (ValueError, TypeError):
        # Fall back to full list if any errors
        full_minutes_list = [f"{m:02d}" for m in range(0, 60, minute_step)]
        end_minute_combo.config(values=full_minutes_list)

# --- Auto Refresh Toggle Function ---
def tog_auto_ref():
    global auto_refresh_todo
    auto_refresh_todo = not auto_refresh_todo
    # Save the setting immediately
    sv_dat(DATA_FILE)

# --- Analysis View Functions ---
def update_analysis_display():
    global current_analysis_date, analysis_view_mode, daily_logs
    global analysis_date_lbl, analysis_plot_type_var, analysis_figure, analysis_canvas_widget
    global analysis_content_frm # Access the global content frame

    # Ensure widgets are ready and matplotlib is available
    if not analysis_date_lbl or not analysis_plot_type_var or not matplotlib_available or not analysis_figure or not analysis_canvas_widget:
        if analysis_date_lbl:
             try:
                 if analysis_view_mode == 'day':
                     display_text = current_analysis_date.strftime("%Y-%m-%d (%A)")
                 elif analysis_view_mode == 'week':
                     start_of_week = current_analysis_date - datetime.timedelta(days=current_analysis_date.weekday())
                     end_of_week = start_of_week + datetime.timedelta(days=6)
                     display_text = f"{start_of_week.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')}"
                 else:
                     display_text = "Invalid View Mode"
                 analysis_date_lbl.config(text=display_text)
             except Exception:
                 if analysis_date_lbl: analysis_date_lbl.config(text="Error")
        return

    # Update date label for either view
    if analysis_view_mode == 'day':
        display_text = current_analysis_date.strftime("%Y-%m-%d (%A)")
        analysis_date_lbl.config(text=display_text)
    elif analysis_view_mode == 'week':
        start_of_week = current_analysis_date - datetime.timedelta(days=current_analysis_date.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        display_text = f"{start_of_week.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')}"
        analysis_date_lbl.config(text=display_text)
    
    # Get reference to the content frame that holds the plot or dashboard
    content_frame = analysis_content_frm 
    
    # Clear existing widgets in content frame
    for widget in content_frame.winfo_children():
        widget.destroy()
    
    if analysis_view_mode == 'day':
        # Implement Day View Dashboard
        create_day_dashboard(content_frame, current_analysis_date)
    else:
        # Week View - Use matplotlib as before
        analysis_figure.clear()
        ax = analysis_figure.add_subplot(111)
        
        plot_type = analysis_plot_type_var.get()
        y_label = "Value"
        plot_title = f"{plot_type}"
        plot_title += f" ({display_text})"
        
        # Dates for the week
        start_of_week = current_analysis_date - datetime.timedelta(days=current_analysis_date.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        dates_in_week = [start_of_week + datetime.timedelta(days=i) for i in range(7)]
        x_dates = dates_in_week
        y_values = []

        # Extract data based on plot_type
        if plot_type == "Tasks Completed":
            y_label = "Tasks Completed (Count)"
            for dt in dates_in_week:
                dt_str = dt.strftime("%Y-%m-%d")
                y_values.append(daily_logs.get(dt_str, {}).get('tasks_completed_count', 0))
        else:
            timer_index = -1
            if plot_type == "Work/Study Time": timer_index = 0
            elif plot_type == "Rest/Entertain Time": timer_index = 1
            elif plot_type == "Sleep/Eat Time": timer_index = 2
            elif plot_type == "Others Time": timer_index = 3

            y_label = "Time Spent (Minutes)"
            timer_index_str = str(timer_index)
            for dt in dates_in_week:
                dt_str = dt.strftime("%Y-%m-%d")
                seconds = daily_logs.get(dt_str, {}).get("timers", {}).get(timer_index_str, 0)
                y_values.append(seconds / 60.0)

        # Plotting
        try:
            ax.plot(x_dates, y_values, marker='o', linestyle='-')
            ax.set_ylabel(y_label)
            ax.set_title(plot_title)
            ax.grid(True, linestyle='--', alpha=0.6)

            # Format x-axis dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%a\n%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator())
            analysis_figure.tight_layout()
            
            # Prepare canvas for matplotlib
            analysis_canvas_widget = FigureCanvasTkAgg(analysis_figure, master=content_frame)
            analysis_canvas_widget_tk = analysis_canvas_widget.get_tk_widget()
            analysis_canvas_widget_tk.pack(side=tki.TOP, fill=tki.BOTH, expand=True)

        except Exception as e:
            print(f"Error generating plot: {e}")
            error_lbl = ttk.Label(content_frame, text=f"Error plotting data: {e}", foreground="red")
            error_lbl.pack(pady=20)

def create_day_dashboard(parent_frame, date):
    # Get day-specific data
    date_str = date.strftime("%Y-%m-%d")
    day_data = daily_logs.get(date_str, {})
    
    # Create scrollable frame for the dashboard
    canvas = tki.Canvas(parent_frame, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
    dashboard_frame = ttk.Frame(canvas)
    
    # Configure canvas
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas_window = canvas.create_window((0, 0), window=dashboard_frame, anchor="nw")
    
    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=event.width)
    
    canvas.bind("<Configure>", on_configure)
    
    # Handle mouse scroll
    def wheel_scroll(event):
        if event.delta:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")
        return "break"
        
    canvas.bind("<MouseWheel>", wheel_scroll)
    canvas.bind("<Button-4>", wheel_scroll)
    canvas.bind("<Button-5>", wheel_scroll)
    
    # Pack scrolling components
    canvas.pack(side=tki.LEFT, fill=tki.BOTH, expand=True)
    scrollbar.pack(side=tki.RIGHT, fill=tki.Y)
    
    title_frame = ttk.Frame(dashboard_frame, padding=10)
    title_frame.pack(fill=tki.X, pady=(0, 10))
    title_label = ttk.Label(title_frame, text=f"Daily Summary - {date_str}", 
                          font=get_scaled_font(scale_factor=1.5))
    title_label.pack()
    
    # Task Completion Section&Data
    task_frame = ttk.LabelFrame(dashboard_frame, text="Task Completion", padding=15)
    task_frame.pack(fill=tki.X, padx=20, pady=10)
    tasks_completed = day_data.get('tasks_completed_count', 0)
    
    # --- Calculate total tasks for the display --- 
    today_str_check = datetime.date.today().strftime("%Y-%m-%d")
    total_tasks = 0
    if date_str == today_str_check:
        total_tasks = len(tasks)
    else:
        total_tasks = tasks_completed
 
    
    # Create task completion display
    if total_tasks > 0:
        completion_percent = (tasks_completed / total_tasks) * 100
        task_info = ttk.Label(task_frame, 
                            text=f"Completed: {tasks_completed} / {total_tasks} tasks ({completion_percent:.1f}%)")
        task_info.pack(pady=5)
        task_progress = ttk.Progressbar(task_frame, orient="horizontal", length=200, mode="determinate", value=completion_percent)
        task_progress.pack(pady=5, fill=tki.X)
    else:
        if date_str == today_str_check:
            ttk.Label(task_frame, text="No tasks yet for today").pack(pady=10)
        else:
            ttk.Label(task_frame, text="No tasks recorded as completed on this day").pack(pady=10)
    
    # Timer Usage& Layout
    timer_frame = ttk.LabelFrame(dashboard_frame, text="Timer Usage", padding=15)
    timer_frame.pack(fill=tki.X, padx=20, pady=10)

    timer_inner_frame = ttk.Frame(timer_frame)
    timer_inner_frame.pack(fill=tki.X, expand=True)
    timer_inner_frame.columnconfigure(0, weight=1)
    timer_inner_frame.columnconfigure(1, weight=1)
    day_timers = day_data.get('timers', {})
    total_seconds = 0
    for timer_id_str, seconds in day_timers.items():
        total_seconds += seconds
    
    # Helper function to format time
    def format_time_display(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
            
    def get_percentage_of_day(seconds):
        day_seconds = 24 * 60 * 60
        return (seconds / day_seconds) * 100
        
    total_time_frame = ttk.Frame(timer_frame, padding=5)
    total_time_frame.pack(fill=tki.X, pady=(0, 10))
    ttk.Label(total_time_frame, text="Total Tracked Time:", font=get_scaled_font(scale_factor=1.1)).pack(side=tki.LEFT, padx=(0, 10))
    
    total_time_str = format_time_display(total_seconds)
    total_percent = get_percentage_of_day(total_seconds)
    
    ttk.Label(total_time_frame, text=f"{total_time_str} ({total_percent:.1f}% of day)", font=get_scaled_font(scale_factor=1.1)).pack(side=tki.LEFT)
    ttk.Separator(timer_frame, orient='horizontal').pack(fill='x', pady=10)
    
    timer_names = {}
    for tmr in timers:
        timer_names[str(tmr['id'])] = tmr['name']
    
    row = 0
    col = 0
    
    # Display timer blocks
    for timer_id_str in sorted(timer_names.keys(), key=int):
        seconds = day_timers.get(timer_id_str, 0)
        timer_name = timer_names.get(timer_id_str, f"Timer {timer_id_str}")
        
        timer_block = ttk.Frame(timer_inner_frame, padding=10, relief="groove", borderwidth=1)
        timer_block.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        ttk.Label(timer_block, text=timer_name, 
                font=get_scaled_font(scale_factor=1.2)).pack(anchor="w")
        
        time_str = format_time_display(seconds)
        ttk.Label(timer_block, text=time_str, 
                font=get_scaled_font(scale_factor=1.4)).pack(pady=5)
        
        if total_seconds > 0:
            percent = (seconds / total_seconds) * 100
            ttk.Label(timer_block, text=f"{percent:.1f}% of tracked time").pack()
            
            # Add mini progress bar
            timer_progress = ttk.Progressbar(timer_block, orient="horizontal", 
                                        length=150, mode="determinate", value=percent)
            timer_progress.pack(pady=5, fill=tki.X)
        else:
            ttk.Label(timer_block, text="0% (no time tracked)").pack()
        
        # Increment grid position
        col += 1
        if col > 1: 
            col = 0
            row += 1
    
    # If no timer data
    if not day_timers:
        no_data_label = ttk.Label(timer_inner_frame, text="No timer data recorded for this day")
        no_data_label.grid(row=0, column=0, columnspan=2, pady=20, sticky=tki.EW)

def change_analysis_date(delta):
    global current_analysis_date, analysis_view_mode

    if analysis_view_mode == 'day':
        current_analysis_date += datetime.timedelta(days=delta)
    elif analysis_view_mode == 'week':
        current_analysis_date += datetime.timedelta(weeks=delta)
        current_analysis_date -= datetime.timedelta(days=current_analysis_date.weekday())

    update_analysis_display()

def toggle_analysis_view():
    global analysis_view_mode

    toggle_btn = None
    if analysis_date_lbl: 
        nav_frame = analysis_date_lbl.master
        for widget in nav_frame.winfo_children():
            if isinstance(widget, ttk.Button) and widget.cget('text').startswith("View:"):
                toggle_btn = widget
                break
                
    if analysis_view_mode == 'day':
        analysis_view_mode = 'week'
        if toggle_btn: toggle_btn.config(text="View: Week")
    else:
        analysis_view_mode = 'day'
        if toggle_btn: toggle_btn.config(text="View: Day")

    update_analysis_display()

# --- Data Persistence Functions ---
def ld_dat(f_path):
    global tasks, timers, minute_step, show_timer_hours, timer_hour_format
    global auto_refresh_todo, last_save_date_str
    global daily_logs 
    global user_name  
    try:
        with open(f_path, 'r', encoding='utf-8') as f:
            loaded_payload = json.load(f)
        loaded_tasks = loaded_payload.get("tasks", [])
        tasks = []
        for task in loaded_tasks:
            task['completion_date'] = task.get('completion_date', None)
            tasks.append(task)

        loaded_timers_data = loaded_payload.get("timers", [])
        tmr_map = {t['id']: t for t in loaded_timers_data}

        for tmr in timers:
            # Keep existing defaults if not found in file
            tmr['last_saved_elapsed'] = tmr.get('elapsed', 0) 
            if tmr['id'] in tmr_map:
                ldd_tmr = tmr_map[tmr['id']]
                tmr['name'] = ldd_tmr.get('name', tmr['name'])
                tmr['elapsed'] = ldd_tmr.get('elapsed', 0)
                tmr['enabled'] = ldd_tmr.get('enabled', True)
                tmr['last_saved_elapsed'] = tmr['elapsed'] 
            tmr['running'] = False 
            tmr['start_time'] = None

        # Load daily logs
        daily_logs = loaded_payload.get("daily_logs", {}) # Load existing logs or default to empty dict

        # Load settings if available
        if "settings" in loaded_payload:
            settings = loaded_payload["settings"]
            minute_step = settings.get('minute_step', 5)
            show_timer_hours = settings.get('show_timer_hours', True)
            timer_hour_format = settings.get('timer_hour_format', 24)
            auto_refresh_todo = settings.get('auto_refresh_todo', False)
            last_save_date_str = settings.get('last_save_date', "")
            user_name = settings.get('user_name', "Friend")  # Load user name

        # --- Daily Refresh Logic ---
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        if auto_refresh_todo and last_save_date_str and last_save_date_str != today_str:
            print(f"Performing daily ToDo refresh (Save date: {last_save_date_str}, Today: {today_str})...")
            tasks = [t for t in tasks if t['completion_date'] is None or t['completion_date'] == today_str]

        print(f"Data loaded from {f_path}")

    except FileNotFoundError:
        # Fresh start with empty data
        tasks = []
        daily_logs = {}
        for tmr in timers:
            tmr['elapsed'] = 0
            tmr['running'] = False
            tmr['start_time'] = None
            tmr['last_saved_elapsed'] = 0 

    except (json.JSONDecodeError, Exception):
        tasks = []
        daily_logs = {}
        for tmr in timers:
            tmr['elapsed'] = 0
            tmr['running'] = False
            tmr['start_time'] = None
            tmr['last_saved_elapsed'] = 0

def sv_dat(f_path):
    global tasks, timers, minute_step, show_timer_hours, timer_hour_format
    global auto_refresh_todo
    global daily_logs 
    global user_name  

    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # AI Using in L1520-1600: Encounter Some complex bugs related to IO&JSON syntax which is fixed by AI
    # --- Update Daily Logs ---
    # Initialize today's log if it doesn't exist
    if today_str not in daily_logs:
        daily_logs[today_str] = {"timers": {}, "tasks_completed_count": 0}

    if "timers" not in daily_logs[today_str]:
        daily_logs[today_str]["timers"] = {}
    any_timer_running = False 
    for tmr in timers:
        if tmr['running']:
            any_timer_running = True
            # Calculate current elapsed time *without* pausing the timer struct itself
            current_elapsed = tmr['elapsed']
            if tmr['start_time']:
                current_elapsed += time.time() - tmr['start_time']

            # Calculate time elapsed since last save
            elapsed_since_save = current_elapsed - tmr.get('last_saved_elapsed', 0)
            if elapsed_since_save < 0: elapsed_since_save = 0 

            # Add to today's log
            timer_id_str = str(tmr['id']) # JSON keys must be strings
            daily_log_timer = daily_logs[today_str]["timers"]
            daily_log_timer[timer_id_str] = daily_log_timer.get(timer_id_str, 0) + elapsed_since_save

            # Update the last saved elapsed time *for the next calculation*
            tmr['last_saved_elapsed'] = current_elapsed

        else:
            # For timers that are not running, ensure their last_saved value matches current value
            tmr['last_saved_elapsed'] = tmr['elapsed']

    # Update tasks completed count for today
    tasks_completed_today = 0
    for task in tasks:
        if task.get('completion_date') == today_str:
            tasks_completed_today += 1
    daily_logs[today_str]['tasks_completed_count'] = tasks_completed_today

    # Prepare timers data for persistence (without runtime state)
    timers_to_persist = []
    for tmr in timers:
        final_elapsed = tmr['elapsed']
        if tmr['running'] and tmr['start_time']:
             final_elapsed += time.time() - tmr['start_time']

        timers_to_persist.append({
            'id': tmr['id'],
            'name': tmr['name'],
            'elapsed': final_elapsed, 
            'enabled': tmr['enabled']
        })
    # Add app settings to payload
    settings = {
        'minute_step': minute_step,
        'show_timer_hours': show_timer_hours,
        'timer_hour_format': timer_hour_format,
        'auto_refresh_todo': auto_refresh_todo,
        'last_save_date': today_str, 
        'user_name': user_name  
    }

    payload = {
        "tasks": tasks, 
        "timers": timers_to_persist,
        "daily_logs": daily_logs, 
        "settings": settings
    }

    try:
        # Use a temporary file and rename to make saving more atomic
        temp_f_path = f_path + ".tmp"
        with open(temp_f_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)
        import os
        os.replace(temp_f_path, f_path)
        print(f"Data saved to {f_path}")
    except Exception as e:
        print(f"Error saving data: {e}")
        # Attempt to remove temporary file if rename failed
        try:
            import os
            if os.path.exists(temp_f_path):
                os.remove(temp_f_path)
        except Exception as e_rem:
            print(f"Error removing temporary save file: {e_rem}")

def hdl_close(win_ref):
    print("Closing application, saving data...")
    # Reset notification state to avoid stale notifications
    global notified_tasks, break_reminder_shown
    notified_tasks = {}
    break_reminder_shown = 0
    
    sv_dat(DATA_FILE)
    win_ref.destroy()

def toggle_focus_mode():
    global focus_panel_frame, pending_area_frame, prog_bar_frame
    
    if focus_panel_frame.winfo_ismapped():
        focus_panel_frame.pack_forget()
        pause_focus_timer() 
    else:
        current_task = find_current_task()
        update_focus_display(current_task)
        focus_panel_frame.pack(side=tki.TOP, fill=tki.X, padx=5, pady=(5, 10), before=prog_bar_frame)

def find_current_task():
    current_time = time.localtime()
    current_hour = current_time.tm_hour
    current_minute = current_time.tm_min
    current_minutes_total = current_hour * 60 + current_minute

    matching_tasks = []
    
    for i, task in enumerate(tasks):
        if task.get('status') == 'pending':
            priority = 0  
            
            start_minutes = None
            end_minutes = None
            
            if task.get('start_time'):
                start_h, start_m = map(int, task['start_time'].split(':'))
                start_minutes = start_h * 60 + start_m
                
            if task.get('end_time'):
                end_h, end_m = map(int, task['end_time'].split(':'))
                end_minutes = end_h * 60 + end_m

            if (start_minutes is not None and end_minutes is not None and start_minutes <= current_minutes_total <= end_minutes):
                priority = 1
                minutes_left = end_minutes - current_minutes_total
                matching_tasks.append((i, task, priority, minutes_left))
                
            elif (start_minutes is not None and 0 <= start_minutes - current_minutes_total <= 15):
                priority = 2
                minutes_until = start_minutes - current_minutes_total
                matching_tasks.append((i, task, priority, minutes_until))
                
            elif (end_minutes is not None and 0 <= end_minutes - current_minutes_total <= 30):
                priority = 3
                minutes_left = end_minutes - current_minutes_total
                matching_tasks.append((i, task, priority, minutes_left))
    
    matching_tasks.sort(key=lambda x: (x[2], x[3]))
    if matching_tasks:
        return matching_tasks[0][0], matching_tasks[0][1]

    for i, task in enumerate(tasks):
        if task.get('status') == 'pending':
            return i, task
            
    return None, None

# Focus mode state management variables
focus_mode_running = False
focus_mode_task_idx = None
focus_mode_start_time = None
focus_mode_elapsed = 0

def update_focus_display(task_data):
    """Updates the focus mode panel with current task information and manages timer state"""
    global focus_title_var, current_task_var, focus_timer_var
    global focus_start_btn, focus_pause_btn, focus_done_btn
    global focus_mode_task_idx, focus_mode_running, focus_mode_start_time, focus_mode_elapsed
    
    new_task_idx, task = task_data
    
    # Reset timer if task has changed
    reset_timer = False
    if new_task_idx != focus_mode_task_idx:
        reset_timer = True
        
        if focus_mode_running:
            pause_focus_timer()
            
    if reset_timer:
        focus_mode_running = False
        focus_mode_start_time = None
        focus_mode_elapsed = 0
        focus_timer_var.set("00:00:00")
        if focus_start_btn: focus_start_btn.config(state=tki.NORMAL if task else tki.DISABLED)
        if focus_pause_btn: focus_pause_btn.config(state=tki.DISABLED)
    focus_mode_task_idx = new_task_idx
    
    # Handle case when no task is available
    if task is None:
        focus_title_var.set("Focus Mode - No Tasks")
        current_task_var.set("Add some tasks to focus on")

        if focus_start_btn: focus_start_btn.config(state=tki.DISABLED)
        if focus_done_btn: focus_done_btn.config(state=tki.DISABLED)

        focus_mode_running = False
        focus_mode_start_time = None
        focus_mode_elapsed = 0
        focus_timer_var.set("00:00:00")
        return
        
    # Update task display information
    task_name = task.get('name', 'Unnamed Task')
    time_info = ""
    
    if task.get('start_time') and task.get('end_time'):
        time_info = f" ({task['start_time']} - {task['end_time']})"
    elif task.get('start_time'):
        time_info = f" (Starts: {task['start_time']})"
    elif task.get('end_time'):
        time_info = f" (Due: {task['end_time']})"
        
    focus_title_var.set("Focus Mode")
    current_task_var.set(f"Current Task: {task_name}{time_info}")
    
    if focus_done_btn: focus_done_btn.config(state=tki.NORMAL)

def start_focus_timer():
    """Starts the focus mode timer and the Work/Study timer simultaneously"""
    global focus_mode_running, focus_mode_start_time, focus_mode_elapsed
    global focus_start_btn, focus_pause_btn
    
    focus_mode_running = True
    focus_mode_start_time = time.time()
    focus_start_btn.config(state=tki.DISABLED)
    focus_pause_btn.config(state=tki.NORMAL)
    
    # Start Work/Study timer (timer 0) automatically
    strt_tmr(0)
    
    update_focus_timer()

def pause_focus_timer():
    """Pauses both the focus timer and Work/Study timer"""
    global focus_mode_running, focus_mode_start_time, focus_mode_elapsed
    global focus_start_btn, focus_pause_btn
    
    if focus_mode_running:
        focus_mode_running = False
        focus_mode_elapsed += time.time() - focus_mode_start_time
        focus_mode_start_time = None
        
        focus_start_btn.config(state=tki.NORMAL)
        focus_pause_btn.config(state=tki.DISABLED)
        
        pse_tmr(0)

def update_focus_timer():
    """Updates timer display and manages break reminders for extended focus sessions"""
    global focus_mode_running, focus_mode_start_time, focus_mode_elapsed
    global focus_timer_var, user_name, break_reminder_shown
    
    if focus_mode_running:
        # Calculate and format elapsed time
        current_time = time.time()
        total_elapsed = focus_mode_elapsed + (current_time - focus_mode_start_time)

        hours = int(total_elapsed // 3600)
        minutes = int((total_elapsed % 3600) // 60)
        seconds = int(total_elapsed % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        focus_timer_var.set(time_str)
        
        # Reminder system: notify after 2 hours of continuous focus
        # and repeat every 5 minutes thereafter
        if (total_elapsed >= 7200 and 
            (break_reminder_shown == 0 or current_time - break_reminder_shown >= 300)):
            break_reminder_shown = current_time
            
            message = f"You've been focusing for {hours} hours, {user_name}! Take a short break to stay productive."
            send_notification(
                title="Break Reminder",
                message=message
            )
        
        if clock_label:
            clock_label.after(1000, update_focus_timer)

def mark_focus_task_done():
    """Marks the current focus task as completed and updates to the next pending task"""
    global focus_mode_task_idx
    
    task_idx, _ = find_current_task()
    
    if task_idx is not None:
        flip_stat(task_idx)
        
        next_task = find_current_task()
        update_focus_display(next_task)
        
        if next_task[1] is None:
            focus_panel_frame.pack_forget()
        
        pause_focus_timer()

# --- Task Notification System ---
# Implements a time-sensitive notification system that alerts users about upcoming tasks
# Uses a priority queue approach to ensure the most urgent notifications are shown first
def check_task_notifications():
    """Scans tasks for time-based notification triggers and schedules future checks"""
    global window, tasks, user_name
    global notified_tasks
    
    current_time = time.time()
    
    # Calculate current time in minutes since midnight for easier time comparisons
    local_time = time.localtime()
    current_hour = local_time.tm_hour
    current_minute = local_time.tm_min
    current_minutes_total = current_hour * 60 + current_minute
    notifications = []
    
    for i, task in enumerate(tasks):
        task_id = f"{i}_{task.get('name', '')}"
        
        if task.get('status') == 'pending':
            start_minutes = None
            
            if task.get('start_time'):
                try:
                    start_h, start_m = map(int, task['start_time'].split(':'))
                    start_minutes = start_h * 60 + start_m
                except (ValueError, TypeError):
                    start_minutes = None
            
            # Notification trigger algorithm:
            # Only notify exactly 5 minutes before or at start time to prevent duplicates
            if start_minutes is not None:
                time_until_start = start_minutes - current_minutes_total
                
                if time_until_start == 5 or time_until_start == 0:
                    notif_key = f"{task_id}_start_{time_until_start}"
                    
                    if notif_key not in notified_tasks:
                        # Create personalized notification message
                        if time_until_start == 0:
                            message = f"It's time to do {task['name']}! Hurry up, {user_name}!"
                        else:
                            message = f"{task['name']} starts in 5 minutes! Get ready, {user_name}!"
                        
                        notifications.append({
                            "task_id": notif_key,
                            "title": "Task Starting Soon" if time_until_start > 0 else "Task Starting Now",
                            "message": message,
                            "priority": time_until_start
                        })
    
    # Sort by priority (most urgent first)
    notifications.sort(key=lambda x: x["priority"])
    
    if notifications:
        notification_data = notifications[0]
        notified_tasks[notification_data["task_id"]] = current_time
        print(f"Notification: {notification_data['title']} - {notification_data['message']}")
        send_notification(
            title=notification_data["title"],
            message=notification_data["message"]
        )
    
    # Schedule frequent checks for better notification timing accuracy
    if window and window.winfo_exists():
        window.after(10000, check_task_notifications)
    
def send_notification(title, message, timeout=10):
    """Sends system notifications with fallback to dialog boxes if needed"""
    if plyer_available:
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="FocusFlow",
                timeout=timeout
            )
            return True
        except Exception as e:
            print(f"Error sending system notification: {e}")
    
    # Fallback notification method using standard dialogs
    try:
        import tkinter.messagebox as messagebox
        messagebox.showinfo(title, message)
        return True
    except Exception as e:
        print(f"Error showing fallback notification: {e}")
        return False

def set_user_name(new_name):
    """Updates the user's name for personalized messages and saves the setting"""
    global user_name
    if new_name and new_name.strip():
        user_name = new_name.strip()
        print(f"User name set to: {user_name}")
        sv_dat(DATA_FILE)
    else:
        user_name = "Friend"
        if user_name_var:
            user_name_var.set(user_name)

def start_edit_todo(idx):
    """Prepares the todo form for editing an existing task"""
    global editing_task_idx, tasks
    global task_name_var, task_content_text, start_hour_var, start_minute_var
    global end_hour_var, end_minute_var, overnight_var
    global new_todo_form_frame
    
    if not (0 <= idx < len(tasks)):
        editing_task_idx = None
        return
        
    editing_task_idx = idx
    task_to_edit = tasks[idx]
    
    # Fill form with task data
    if task_name_var: task_name_var.set(task_to_edit.get("name", ""))
    if task_content_text:
        task_content_text.delete("1.0", tki.END)
        task_content_text.insert("1.0", task_to_edit.get("content", ""))
    
    # Parse and set time fields
    start_time = task_to_edit.get("start_time")
    end_time = task_to_edit.get("end_time")
    is_overnight = task_to_edit.get("overnight", False)
    
    if start_hour_var: start_hour_var.set(start_time.split(':')[0] if start_time else "")
    if start_minute_var: start_minute_var.set(start_time.split(':')[1] if start_time else "")
    if end_hour_var: end_hour_var.set(end_time.split(':')[0] if end_time else "")
    if end_minute_var: end_minute_var.set(end_time.split(':')[1] if end_time else "")
    
    if overnight_var:
        overnight_var.set(is_overnight)
    
    # Update time dropdowns with appropriate constraints
    upd_end_hrs()
    
    # Display the form if currently hidden
    if new_todo_form_frame and not new_todo_form_frame.winfo_ismapped():
        toggle_new_todo_form()

if __name__=="__main__": main() 
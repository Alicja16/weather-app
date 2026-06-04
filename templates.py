import customtkinter
from datetime import datetime
import API_queries
from analysis import Current_Table_form, Chart_form, Table_form
from typing import Literal
import threading

class Checkbox_frame(customtkinter.CTkScrollableFrame):
    def __init__(self,master, title:str, values: list):
        super().__init__(master)

        self.grid_columnconfigure(0, weight=1)
        self.title = title
        self.values = values
        self.checkboxes = []

        self.title = customtkinter.CTkLabel(self, text=self.title, fg_color="gray30", corner_radius=6)
        self.title.grid(row=0, column=0, padx=(10), pady=(10,0), sticky="ew")


        for i, value in enumerate(self.values):
            checkbox =customtkinter.CTkCheckBox(self, text=value)
            checkbox.grid(row=i+1, column=0, padx=(10), pady=(10,0), sticky="w")
            self.checkboxes.append(checkbox)
        
    def get_checked(self):
        checked_checkboxes = []
        for i in self.checkboxes:
            if i.get() == 1:
                checked_checkboxes.append(i.cget("text"))
        return checked_checkboxes
    
    def change_state_of_checkbox(self, checkboxes: list, new_state: Literal['normal', 'disabled']):
        for checkbox in self.checkboxes:
            if checkbox.cget("text") in checkboxes:
                if new_state=="disabled":
                    checkbox.deselect()
                checkbox.configure(state=new_state)
    



class Radio_button_frame(customtkinter.CTkFrame):
    def __init__(self, master, title: str, values: list, controller):
        super().__init__(master)

        self.grid_columnconfigure(0, weight=1)
        self.title = title
        self.values = values
        self.radio_buttons = []
        self.variable = customtkinter.StringVar(value="")

        self.controller = controller

        self.title = customtkinter.CTkLabel(self, text=self.title, fg_color="gray30", corner_radius=6)
        self.title.grid(row=0, column=0, padx=(10), pady=(10,0), sticky="ew")

        for i, value in enumerate(self.values):
            radio_button = customtkinter.CTkRadioButton(self, text=value, value=value, variable=self.variable, command=controller)
            radio_button.grid(row=i+1, column=0, padx=(10), pady=(10,0), sticky="w")
            self.radio_buttons.append(radio_button)
    
    def get(self):
        return self.variable.get()
    
    def set(self, value):
        self.variable.set(value)


class Buttons_frame(customtkinter.CTkFrame):
    def __init__(self, master, title: str, values: list, callback):
        super().__init__(master)
        self.title = title
        self.values = values
        self.callback = callback

        for _,i in enumerate(self.values):
            option = (str(i[0])+', '+str(i[1])+', '+str(i[2])+' ('+str(i[3])+', '+str(i[4])+')')
            print(option)
            new_button = customtkinter.CTkButton(self, text=option, command=lambda v=i: self.get_result(v, option))
            new_button.pack(pady=5, fill = "x")
    

    def get_result(self, value_list, value_text):
        self.callback(value_list, value_text)
        self.master.destroy()
        return
    



class ToplevelWindow(customtkinter.CTkToplevel):
    def __init__(self, master, text):
        super().__init__()
        self.text = text
        self.master = master
        self.protocol("WM_DELETE_WINDOW", self.close)
    
    def adjust_size(self):
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        self.geometry(f"{w}x{h}")
        self.minsize(w, h)
    
    def im_primary_window(self):
        self.transient(self.master)
        self.grab_set()
        self.adjust_size()
        self.focus_get()
        self.bind()
    
    def close(self):
        try:
            self.grab_release()
        except Exception:
            pass

        self.destroy()


class Search_ToplevelWindow(ToplevelWindow):
    def __init__(self, master, text, values:list, callback):
        super().__init__(master, text)
        self.callback = callback
        self.values = values
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.exact_location = Buttons_frame(self, self.text, self.values, self.callback)
        self.exact_location.pack(padx=10, pady=10)

        


class Search_frame(customtkinter.CTkFrame):
    def __init__(self, master, placeholder: str, button_text: str):
        super().__init__(master)
        self.master = master
        self.placeholder=placeholder
        self.button_text=button_text
        self.grid_columnconfigure(0, weight=1)

        self.search = customtkinter.CTkEntry(self, placeholder_text=self.placeholder)
        self.search.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.search_button = customtkinter.CTkButton(self, text=self.button_text, command=self.search_button_callback, width=120)
        self.search_button.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        self.location_window = None
        self.choice = [None]
    

    def search_button_callback(self, limit=5):
        if self.location_window is None or not self.location_window.winfo_exists():
            city_name = self.search.get()

            self.search_button.configure(state="disabled", text="Searching...")

            threading.Thread(
                target = self.search_worker,
                args=(city_name, limit),
                daemon=True
            ).start()
            
        else:
            self.location_window.bind()


    def search_worker(self, city_name, limit=5):
        try:
            location_list = API_queries.check_coordinates(city_name, limit)
            self.after(0, lambda: self.show_location_window(location_list))

        except Exception as e:
            self.after(0, lambda err=e: self.show_search_error(err))
    

    def show_search_error(self, error):
        self.search_button.configure(
            state="normal",
            text=self.button_text
        )

        print(f"Search error: {error}")


    def show_location_window(self, location_list):
        self.search_button.configure(
            state="normal",
            text=self.button_text
        )

        if not location_list:
            print("No locations found.")
            return

        self.location_list = location_list

        self.location_window = Search_ToplevelWindow(
            self.master,
            "Choose location",
            self.location_list,
            self.change_choice_text
        )

        self.location_window.im_primary_window()
        print(self.location_list)


    def change_choice_text(self, value_list, value_text):
        self.choice = value_list
        self.search.delete(0, "end")
        self.search.insert(0, value_text)
        print(value_text)


    def get_chosen_location(self):
        if not isinstance(self.choice, list) or len(self.choice) < 5:
            return None

        return (self.choice[3], self.choice[4])


class Clock_frame(customtkinter.CTkFrame):
    def __init__(self, master, chosen_location, format:str = "%d.%m.%Y %H:%M:%S", refresh_ms: int = 1000):
        super().__init__(master)
        self.grid_rowconfigure((0), weight=1)
        self.grid_columnconfigure((0,1,2), weight=1)

        self.format = format
        self.chosen_location = chosen_location
        self.refresh_ms = refresh_ms

        self._running = True
        self._tick_after_id = None

        self.clock = customtkinter.CTkLabel(
            self,
            text=datetime.now().strftime(self.format),
            fg_color="gray30",
            corner_radius=6
        )

        self.clock.grid(row=0, column=1, padx=10, pady=10)
        self.bind("<Destroy>", self.on_destroy, add="+")
        self.tick()

    def tick(self):
        if not self._running:
            return

        try:
            self.chosen_location = self.master.get_chosen_location()

            if self.chosen_location is not None:
                current_time = API_queries.get_time_coords(
                    self.chosen_location[0],
                    self.chosen_location[1]
                )
            else:
                current_time = datetime.now().strftime(self.format)

            if not self._running:
                return

            self.clock.configure(text=current_time)

            self._tick_after_id = self.after(
                self.refresh_ms,
                self.tick
            )

        except Exception as e:
            if self._running:
                print(f"Clock error: {e}")

    def stop(self):
        self._running = False

        if self._tick_after_id is not None:
            try:
                self.after_cancel(self._tick_after_id)
            except Exception:
                pass

            self._tick_after_id = None

    def on_destroy(self, event):
        if event.widget is self:
            self.stop()





class Tabview_frame(customtkinter.CTkFrame):
    def __init__(self, master, tabs: list):
        super().__init__(master)
        self.grid_rowconfigure((0), weight=1)
        self.grid_columnconfigure((0), weight=1)
        self.tabs = tabs

        self.tabview = customtkinter.CTkTabview(self, corner_radius=20, border_width=5, command=self.get_current_tab)
        for tab in self.tabs:
            self.tabview.add(tab)
        self.tabview.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

    def get_current_tab(self):
        print(self.tabview.get())
        self.master.adjust_size()
        return self.tabview.get()
    
    def set_tab_view(self, tab_name, View_Class, **kwargs):
        tab_container = self.tabview.tab(tab_name)
        view = View_Class(tab_container, **kwargs)
        view.pack(fill="both", expand=True)
        return view
    

class Result_ToplevelWindow(ToplevelWindow):
    def __init__(self, master, text, tabs:list, values:list, mode:Literal["Table", "Chart+Table"], img=None, icons=None):
        super().__init__(master, text)
        self.tabs = tabs
        self.values = values
        self.icons = icons or {}
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tabframe = Tabview_frame(self, self.tabs)
        self.tabframe.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        if mode == "Table":
            for i, t in enumerate(self.tabs):
                if t == "Weather":
                    self.tabframe.set_tab_view(t, Current_Table_form, values=values[i], img=img)
                else:
                    self.tabframe.set_tab_view(t, Current_Table_form, values=values[i])
        elif mode == "Chart+Table":
            for i, t in enumerate(self.tabs):
                if t == "weather":
                    self.tabframe.set_tab_view(t, Table_form, values=values[i], icons=self.icons)
                else:
                    self.tabframe.set_tab_view(t, Chart_form, values=values[i], label=t)




        
        
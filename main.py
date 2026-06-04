import customtkinter
from datetime import date
import pprint
import API_queries
import templates
from data import *
import threading
import matplotlib.pyplot as plt
# https://openweathermap.org/api/one-call-3?collePction=one_call_api_3.0


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.chosen_location = None
        self.chosen_option = None
        self.chosen_parameters = []
        self.chosen_start_date = None
        self.chosen_end_date = None

        self.title("Weather App")
        self.geometry("800x600")

        self.is_closing = False
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.grid_columnconfigure((0,1), weight=1, uniform="cols")
        self.grid_rowconfigure((2), weight=1)

        self.search = templates.Search_frame(self, "Search city...", "Search location")
        self.search.grid(row=0, column=0, padx=10, pady=10, sticky="ew", columnspan=2)

        self.clock = templates.Clock_frame(self,self.chosen_location)
        self.clock.grid(row=1, column=0, padx=10, pady=10, sticky="ew", columnspan=2)

        Parameters=(p for p in Params.keys())
        self.weather_parameters = templates.Checkbox_frame(self, "Parameters", Parameters)
        self.weather_parameters.grid(row=2, column=1, padx=10, pady=(10,0), sticky="nsew")

        self.forecast_type = templates.Radio_button_frame(self, "Forecast",Weather_options, self.correct_available_parameters)
        self.forecast_type.grid(row=2, column=0, padx=10, pady=(10,0), sticky="nsew")

        self.download_button = customtkinter.CTkButton(self, text="Download weather", command=self.download_button_callback)
        self.download_button.grid(row=4, column=0, padx=10, pady=10, sticky="ew", columnspan=2)


    def on_close(self):
        self.is_closing = True

        try:
            self.clock.stop()
        except Exception:
            pass

        # Zamknij wszystkie okna Toplevel przed zniszczeniem głównej aplikacji
        try:
            for widget in list(self.winfo_children()):
                if isinstance(widget, customtkinter.CTkToplevel):
                    try:
                        widget.close()
                    except AttributeError:
                        widget.destroy()
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            plt.close("all")
        except Exception:
            pass

        try:
            self.quit()
        except Exception:
            pass

        try:
            self.destroy()
        except Exception:
            pass


    def get_chosen_location(self):
        self.chosen_location = self.search.get_chosen_location()
        return self.chosen_location
    


    def download_button_callback(self):
        self.chosen_location = self.search.get_chosen_location()
        self.chosen_option = self.forecast_type.get()
        self.chosen_parameters = self.weather_parameters.get_checked()

        if self.chosen_location is None:
            print("Choose location")
            return

        if not self.chosen_option:
            print("Choose forecast type")
            return

        if not self.chosen_parameters:
            print("Choose parameters")
            return

        print(f"Wybrana opcja: {self.chosen_option}")
        print(f"Parametry: {self.chosen_parameters}")

        self.download_button.configure(
            state="disabled",
            text="Downloading..."
        )

        threading.Thread(target=self.download_weather_worker, daemon=True).start()

        
    def download_weather_worker(self):
        try:
            result = None

            if self.chosen_option == "Current weather":
                result = API_queries.get_current_weather(self.chosen_location[0],
                                                self.chosen_location[1],
                                                self.chosen_parameters)
                
            elif self.chosen_option == "Hourly forecast up to 4 days":
                result = API_queries.get_hourly_forecast(self.chosen_location[0],
                                                self.chosen_location[1],
                                                self.chosen_parameters)
                
            elif self.chosen_option == "Daily forecast up to 16 days":
                result = API_queries.get_daily_forecast(self.chosen_location[0],
                                            self.chosen_location[1],
                                            self.chosen_parameters)# amount of days (1-16)
            
            elif self.chosen_option == "3-hour step forecast to 5 days":
                result = API_queries.get_3_hourly_forecast(self.chosen_location[0],
                                                self.chosen_location[1],
                                                self.chosen_parameters)# amount of timestamps (1-40)
            
            elif self.chosen_option == "Climate forecast for 30 days":
                result = API_queries.get_climatic_forecast(self.chosen_location[0],
                                                self.chosen_location[1],
                                                self.chosen_parameters)
            else:
                result = None
            
            if result is not None:
                result["icons"] = API_queries.preload_icons_for_result(result)

            if not self.is_closing:
                self.after(0, lambda result=result: self.show_weather_result(result))
            
        except Exception as e:
            if not self.is_closing:
                self.after(0, lambda err=e: self.show_download_error(err))
    

    def show_weather_result(self, result):
        if result is None:
            self.download_button.configure(
                state="normal",
                text="Download weather"
            )
            print("There is nothing to show.")
            return
        
        img = None

        if result.get("icon_id") is not None:
            icon_id = result["icon_id"]
            pil_img = result.get("icons", {}).get((icon_id, (100, 100)))
            img = API_queries.make_ctk_icon(pil_img)
        
        result_window = templates.Result_ToplevelWindow(
            self,
            result["title"],
            result["tabs"],
            result["values"],
            mode=result["mode"],
            img=img,
            icons=result.get("icons", {})
        )
        result_window.im_primary_window()

        self.download_button.configure(
            state="normal",
            text="Download weather"
        )


    def show_download_error(self, error):
        self.download_button.configure(
            state="normal",
            text="Download weather"
        )

        print(f"Błąd pobierania danych: {error}")


    def correct_available_parameters(self):
        self.chosen_option = self.forecast_type.get()
        change = ["air pollution","sunrise","sunset"]
        if self.chosen_option != "Current weather":
            self.weather_parameters.change_state_of_checkbox(change, new_state="disabled")
        else:
            self.weather_parameters.change_state_of_checkbox(change, new_state="normal")

app = App()
app.mainloop()
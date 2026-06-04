import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import numpy as np
import customtkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import API_queries
from CTkRangeSlider import *
from data import *

class Range_Slider():
    def __init__(self, master, from_, to, number_of_steps, command_released):
        self.slider = CTkRangeSlider(master=master,
                                    from_=from_,
                                    to=to,
                                    number_of_steps=number_of_steps)
        self.slider.pack(padx=10, pady=10, fill="both")
        self.slider.bind("<ButtonRelease-1>", self.slider_released)
        self.command_released = command_released
    
    def slider_released(self, event):
        start, end = self.slider.get()
        start = int(start)
        end = int(end)
        print(f"Slider: {start, end}")
        self.command_released(start, end)


class Current_Table_form(customtkinter.CTkFrame):
    def __init__(self, master, values, img=None):
        super().__init__(master)
        self.values = values

        self.grid_columnconfigure((0,1), weight=1)

        if img != None:
            self.img_label = customtkinter.CTkLabel(self, image=img, text="")
            self.img_label.grid(row=0, column=0, padx=10, pady=10, columnspan=2)

        self.label_values = []

        for i, value in enumerate(self.values):
            label_p =customtkinter.CTkLabel(self, text=value[0])
            label_p.grid(row=i+1, column=0, padx=(10), pady=(0), sticky="nsew")
            label_v =customtkinter.CTkLabel(self, text=value[1])
            label_v.grid(row=i+1, column=1, padx=(10), pady=(0), sticky="nsew")
            self.label_values.append((label_p, label_v))


class Chart_form(customtkinter.CTkFrame):
    def __init__(self, master, values: list, label:str, label_time: str = "Time"):
        super().__init__(master)
        self.time, self.y = zip(*values)

        y_min = min(self.y)
        y_max = max(self.y)
        margin = (y_max - y_min)*0.1

        margin = 1 if margin ==0 else margin

        self.y_range = (min(self.y)-margin, max(self.y)+margin)
        self.label_y = Params[label][-1]

        self.slider = Range_Slider(self, 0, len(self.time), len(self.time), self.update_axes)

        plt.style.use('Solarize_Light2')

        self.fig = Figure(
            figsize=(10, 5),
            constrained_layout=True
        )

        self.axs = self.fig.subplot_mosaic(
            [
                ['A', 'A', 'A', 'B', 'B'],
                ['A', 'A', 'A', 'C', 'C']
            ],
            gridspec_kw={
                "width_ratios": [3, 3, 3, 1.5, 1.5]
            }
        )
        
        self.line, = self.axs['A'].plot(self.time, self.y, "-o", label=label)
        self.axs['A'].set_ylim(self.y_range[0], self.y_range[1])
        self.axs['A'].fill_between(self.time, self.y, alpha=0.3, label="_nonlegend_")
        self.axs['A'].xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
        self.axs['A'].grid(True, alpha=0.3)
        self.axs['A'].set_title(label)
        self.axs['A'].set_xlabel(label_time)
        self.axs['A'].set_ylabel(self.label_y)
        self.axs['A'].legend()

        _, _, self.hist_patches = self.axs['B'].hist(self.y, bins=10, alpha=0.8, edgecolor="black", density=True)
        self.axs['B'].set_title(f"Histogram")
        self.axs['B'].set_xlabel(label)
        self.axs['B'].set_ylabel("Amount")

        self.boxplot_artists = self.axs['C'].boxplot(self.y, widths=0.6)
        self.axs['C'].set_title(f"Statistics")

        self.fig.autofmt_xdate()
        # self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.bind("<Destroy>", self.on_destroy, add="+")
    

    def on_destroy(self, event):
        if event.widget is not self:
            return

        try:
            self.canvas.get_tk_widget().destroy()
        except Exception:
            pass

        try:
            self.fig.clear()
        except Exception:
            pass

        try:
            plt.close(self.fig)
        except Exception:
            pass
    

    def update_axes(self, start, end):
        new_time = self.time[start:end+1]
        new_values = self.y[start:end+1]
        self.line.set_data(new_time, new_values)

        self.axs['A'].set_xlim(new_time[0], new_time[-1])
        self.axs['A'].relim()
        self.axs['A'].autoscale_view(scalex=False, scaley=True)

        for patch in self.hist_patches:
            patch.remove()
        
        _, _, self.hist_patches = self.axs['B'].hist(new_values, bins=10, alpha=0.8, edgecolor="black", density=True)
        self.axs['B'].relim()
        self.axs['B'].autoscale_view()

        for art_values in self.boxplot_artists.values():
            for art_value in art_values:
                art_value.remove()


        self.boxplot_artists = self.axs['C'].boxplot(new_values, widths=0.6)
        self.axs['C'].relim()
        self.axs['C'].autoscale_view()

        self.fig.canvas.draw_idle()



class Table_form(customtkinter.CTkScrollableFrame):
    def __init__(self, master, values,  icons=None):
        super().__init__(master)
        self.values = values
        self.icons = icons or {}

        self.grid_columnconfigure((0,1,2), weight=1)

        self.label_values = []
        self.images = []

        for i, value in enumerate(self.values):
            label_p =customtkinter.CTkLabel(self, text=value[0])
            label_p.grid(row=i+1, column=0, padx=(10), pady=(0), sticky="nsew")

            label_v =customtkinter.CTkLabel(self, text=value[1])
            label_v.grid(row=i+1, column=1, padx=(10), pady=(0), sticky="nsew")

            row = (label_p, label_v)

            if len(value) > 2:
                icon_id = value[2]
                pil_img = self.icons.get((icon_id, (50, 50)))
                img = API_queries.make_ctk_icon(pil_img)

                if img is not None:
                    self.images.append(img)

                    label_img = customtkinter.CTkLabel(self, image=img, text="")
                    label_img.grid(row=i+1, column=2, padx=10, pady=0, sticky="nsew")

                    row = (label_p, label_v, label_img)

            self.label_values.append(row)

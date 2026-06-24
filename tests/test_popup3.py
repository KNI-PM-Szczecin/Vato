import customtkinter as ctk
import time
from views.popup import PopupMessage

ctk.set_appearance_mode("System")
app = ctk.CTk()
app.geometry("400x400")

def simulate_bug():
    # simulate the exact same flow
    PopupMessage("Warning", "TTS Busy", status="warning")

btn = ctk.CTkButton(app, text="Simulate", command=simulate_bug)
btn.pack(pady=50)

# I will programmatically trigger the popup
app.after(500, simulate_bug)

# Programmatically trigger the button click
def click_ok():
    for child in app.winfo_children():
        if isinstance(child, ctk.CTkToplevel):
            # Find the OK button
            for widget in child.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for btn_frame in widget.winfo_children():
                        if isinstance(btn_frame, ctk.CTkFrame):
                            for btn in btn_frame.winfo_children():
                                if isinstance(btn, ctk.CTkButton) and btn.cget("text") == "Zrozumiałem":
                                    print("Found OK button, invoking!")
                                    btn._command()
                                    return

app.after(1000, click_ok)

def check_alive():
    count = sum(1 for c in app.winfo_children() if isinstance(c, ctk.CTkToplevel))
    print(f"TopLevels alive after click: {count}")
    app.destroy()

app.after(1500, check_alive)

app.mainloop()

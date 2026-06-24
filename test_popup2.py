import customtkinter as ctk
from views.popup import PopupMessage

ctk.set_appearance_mode("System")
app = ctk.CTk()
app.geometry("400x400")

def show_popup():
    p = PopupMessage("Test", "Click OK to close this", status="warning")

btn = ctk.CTkButton(app, text="Show Popup", command=show_popup)
btn.pack(pady=50)

app.after(500, show_popup)

# We will let it run for 4 seconds so I can see if it crashes.
app.after(4000, app.destroy)
app.mainloop()

from PIL import Image, ImageTk
from io import BytesIO
import requests
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

data = []

# Получение данных
try:
    response = requests.get('http://omsktec-playgrounds.ru/algos/lab13', verify=False)
    if response.status_code == 200:
        data = response.json()
    else:
        print(f"Ошибка сервера: {response.status_code}")
except Exception as e:
    print(f'Ошибка загрузки данных: {e}')

def format_duration(ms):
    seconds = int(ms / 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"

def search_song(event=None):
    search_term = search_entry.get().lower()
    hide_explicit = hide_explicit_var.get()
    
    for item in table.get_children():
        table.delete(item)
    
    if not data:
        return
        
    for item in data:
        track = item['track']
        if hide_explicit and track.get('explicit', False):
            continue
            
        if (not search_term or 
            search_term in track['name'].lower() or 
            search_term in track['artists'][0]['name'].lower() or 
            search_term in track['album']['name'].lower()):
            
            table.insert('', tk.END, values=(
                track['name'],
                ", ".join([a['name'] for a in track['artists']]),
                format_duration(track['duration_ms']),
                track['album']['name']
            ))

def sort_song(event=None):
    selected_sort = sort_combobox.get()
    if not data:
        return
        
    sorted_data = data.copy()
    
    if selected_sort == 'По дате выхода':
        sorted_data.sort(key=lambda x: x['track']['album']['release_date'], reverse=True)
    elif selected_sort == 'По популярности':
        sorted_data.sort(key=lambda x: x['track']['popularity'], reverse=True)
    elif selected_sort == 'По длительности':
        sorted_data.sort(key=lambda x: x['track']['duration_ms'], reverse=True)
    
    for item in table.get_children():
        table.delete(item)
    
    for item in sorted_data:
        track = item['track']
        table.insert('', tk.END, values=(
            track['name'],
            ", ".join([a['name'] for a in track['artists']]),
            format_duration(track['duration_ms']),
            track['album']['name']
        ))

def on_item_select(event):
    selected_items = table.selection()
    if not selected_items:
        return
        
    item = table.item(selected_items[0])
    track_name = item['values'][0]
    artist_name = item['values'][1]
    
    for track in data:
        if (track['track']['name'] == track_name and 
            ", ".join([a['name'] for a in track['track']['artists']]) == artist_name):
            display_track_details(track['track'])
            break

def display_track_details(track):
    # Данные о треке
    details_text.set(
        f"{track['name']}\n\n"
        f"Исполнитель: {', '.join([a['name'] for a in track['artists']])}\n"
        f"Альбом: {track['album']['name']}\n"
        f"Длительность: {format_duration(track['duration_ms'])}\n"
        f"Популярность: {track['popularity']}\n"
        f"Дата релиза: {track['album']['release_date']}\n"
        f"Explicit: {'Да' if track.get('explicit', False) else 'Нет'}"
    )
    
    # Обложка
    if track['album']['images']:
        load_cover(track['album']['images'][0]['url'])

def load_cover(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            image = image.resize((200, 200), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            cover_label.config(image=photo)
            cover_label.image = photo
    except Exception as e:
        print(f"Ошибка загрузки обложки: {e}")

root = tk.Tk()
root.title("Просмотр треков Spotify")
root.geometry("1000x700")
root.configure(bg="white")

# Стилевые
style = ttk.Style()
style.configure("TFrame", background="white")
style.configure("TLabel", background="white", font=("Arial", 10))
style.configure("TButton", font=("Arial", 10))
style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

# Панелька
control_frame = ttk.Frame(root, padding=10)
control_frame.pack(fill=tk.X)

ttk.Label(control_frame, text="Поиск:").pack(side=tk.LEFT)
search_entry = ttk.Entry(control_frame, width=40)
search_entry.pack(side=tk.LEFT, padx=5)
search_entry.bind("<KeyRelease>", search_song)

ttk.Label(control_frame, text="Сортировка:").pack(side=tk.LEFT, padx=(10, 0))
sort_combobox = ttk.Combobox(control_frame, values=[
    "По дате выхода", "По популярности", "По длительности"
], state="readonly")
sort_combobox.pack(side=tk.LEFT)
sort_combobox.set("По дате выхода")
sort_combobox.bind("<<ComboboxSelected>>", sort_song)

hide_explicit_var = tk.IntVar()
hide_explicit_check = ttk.Checkbutton(
    control_frame, 
    text="Скрыть explicit треки", 
    variable=hide_explicit_var,
    command=search_song
)
hide_explicit_check.pack(side=tk.LEFT, padx=10)

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

table_frame = ttk.Frame(main_frame)
table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

table = ttk.Treeview(table_frame, columns=("title", "artist", "duration", "album"), show="headings")
table.heading("title", text="Название песни")
table.heading("artist", text="Исполнитель")
table.heading("duration", text="Длительность")
table.heading("album", text="Альбом")

table.column("title", width=250)
table.column("artist", width=150)
table.column("duration", width=80, anchor=tk.CENTER)
table.column("album", width=200)

table.pack(fill=tk.BOTH, expand=True)
table.bind("<<TreeviewSelect>>", on_item_select)

# Инфа о треке
details_frame = ttk.Frame(main_frame, width=250)
details_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

# Обложка
cover_frame = ttk.Frame(details_frame)
cover_frame.pack(pady=10)
cover_label = ttk.Label(cover_frame)
cover_label.pack()

# Информация о треке
details_text = tk.StringVar()
details_label = ttk.Label(
    details_frame, 
    textvariable=details_text, 
    wraplength=230, 
    justify=tk.LEFT
)
details_label.pack(fill=tk.X, pady=10)

# Загрузка данных о треках
search_song()

root.mainloop()

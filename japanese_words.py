import tkinter as tk
from tkinter import ttk
import random
import json
from gtts import gTTS
import os
import tempfile
import pygame
import time
import sys

class JapaneseWordsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Изучение японских слов")
        self.root.geometry("800x600")
        
        # Настройка масштабирования
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Инициализация pygame для воспроизведения звука
        pygame.mixer.init()
        
        # Определение пути к JSON файлу
        if getattr(sys, 'frozen', False):
            # Если приложение упаковано в EXE
            application_path = sys._MEIPASS
        else:
            # Если запущено как Python скрипт
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        json_path = os.path.join(application_path, 'japanese_words.json')
        
        # Загрузка слов из JSON файла
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.words_data = json.load(f)
        except Exception as e:
            tk.messagebox.showerror("Ошибка", f"Не удалось загрузить файл данных: {str(e)}")
            self.words_data = {}
        
        # Создание временной директории для аудио файлов
        self.temp_dir = tempfile.mkdtemp()
        
        # Флаг воспроизведения
        self.is_playing = False
        
        # Текущий индекс слова для режима изучения
        self.current_word_index = 0
        self.current_category = None
        
        # Создание стилей
        self.create_styles()
        
        # Создание интерфейса
        self.create_widgets()
        
    def create_styles(self):
        # Создание стилей для виджетов
        style = ttk.Style()
        
        # Стиль для меток
        style.configure('Large.TLabel', font=('Arial', 32))
        style.configure('Medium.TLabel', font=('Arial', 24))
        style.configure('Normal.TLabel', font=('Arial', 16))
        
        # Стиль для кнопок
        style.configure('Large.TButton', font=('Arial', 14))
        
        # Стиль для комбобокса
        style.configure('Large.TCombobox', font=('Arial', 14))
        
    def create_widgets(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка масштабирования для main_frame
        for i in range(9):  # 9 строк в main_frame
            main_frame.grid_rowconfigure(i, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Выбор категории
        ttk.Label(main_frame, text="Выберите категорию:", style='Normal.TLabel').grid(row=0, column=0, pady=20, padx=10, sticky='w')
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(main_frame, textvariable=self.category_var, values=list(self.words_data.keys()), style='Large.TCombobox', width=40)
        self.category_combo.grid(row=0, column=1, pady=20, padx=10, sticky='ew')
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_select)
        
        # Переключатель режима
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=1, column=0, columnspan=2, pady=10)
        self.mode_var = tk.StringVar(value="study")
        ttk.Radiobutton(mode_frame, text="Режим изучения", variable=self.mode_var, value="study", command=self.change_mode, style='Normal.TLabel').grid(row=0, column=0, padx=20)
        ttk.Radiobutton(mode_frame, text="Режим тестирования", variable=self.mode_var, value="test", command=self.change_mode, style='Normal.TLabel').grid(row=0, column=1, padx=20)
        
        # Метка с японским словом
        self.japanese_label = ttk.Label(main_frame, text="", style='Large.TLabel')
        self.japanese_label.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Метка с ромадзи
        self.romaji_label = ttk.Label(main_frame, text="", style='Medium.TLabel')
        self.romaji_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Кнопка озвучки
        self.sound_button = ttk.Button(main_frame, text="🔊", command=self.play_sound, style='Large.TButton')
        self.sound_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Поле для ввода ответа
        self.answer_frame = ttk.Frame(main_frame)
        self.answer_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Label(self.answer_frame, text="Ваш ответ:", style='Normal.TLabel').grid(row=0, column=0, padx=10)
        self.answer_entry = ttk.Entry(self.answer_frame, width=40, font=('Arial', 14))
        self.answer_entry.grid(row=0, column=1, padx=10)
        self.answer_entry.bind('<Return>', self.check_answer)
        
        # Метка с переводом
        self.translation_label = ttk.Label(main_frame, text="", style='Medium.TLabel', wraplength=600)
        self.translation_label.grid(row=6, column=0, columnspan=2, pady=20)
        
        # Кнопки
        self.buttons_frame = ttk.Frame(main_frame)
        self.buttons_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        self.show_button = ttk.Button(self.buttons_frame, text="Показать перевод", command=self.show_translation, style='Large.TButton')
        self.show_button.grid(row=0, column=0, padx=10)
        
        self.next_button = ttk.Button(self.buttons_frame, text="Следующее слово", command=self.show_next_word, style='Large.TButton')
        self.next_button.grid(row=0, column=1, padx=10)
        
        self.check_button = ttk.Button(self.buttons_frame, text="Проверить", command=lambda: self.check_answer(None), style='Large.TButton')
        self.check_button.grid(row=0, column=2, padx=10)
        
        # Статистика
        self.stats_label = ttk.Label(main_frame, text="", style='Normal.TLabel')
        self.stats_label.grid(row=8, column=0, columnspan=2, pady=20)
        
        # Инициализация статистики
        self.correct_answers = 0
        self.total_questions = 0
        
        # Инициализация режима
        self.change_mode()
        
    def play_sound(self):
        if hasattr(self, 'current_word') and not self.is_playing:
            self.is_playing = True
            self.sound_button.config(state='disabled')  # Отключаем кнопку на время воспроизведения
            
            try:
                # Создаем временный файл для аудио
                temp_file = os.path.join(self.temp_dir, 'temp.mp3')
                
                # Если файл существует, удаляем его
                if os.path.exists(temp_file):
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                    os.remove(temp_file)
                
                # Создаем новый аудио файл
                tts = gTTS(text=self.current_word[1]['romaji'], lang='ja')
                tts.save(temp_file)
                
                # Воспроизводим звук
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                
                # Ждем окончания воспроизведения
                self.root.after(100, self.check_sound_finished)
            except Exception as e:
                print(f"Ошибка воспроизведения: {e}")
                self.is_playing = False
                self.sound_button.config(state='normal')
    
    def check_sound_finished(self):
        if pygame.mixer.music.get_busy():
            self.root.after(100, self.check_sound_finished)
        else:
            pygame.mixer.music.unload()
            self.is_playing = False
            self.sound_button.config(state='normal')  # Включаем кнопку обратно
        
    def change_mode(self):
        mode = self.mode_var.get()
        if mode == "study":
            self.answer_frame.grid_remove()
            self.check_button.grid_remove()
            self.show_button.grid_remove()  # Убираем кнопку показа перевода в режиме изучения
            self.translation_label.grid()
            self.stats_label.config(text="")
            self.correct_answers = 0
            self.total_questions = 0
        else:
            self.answer_frame.grid()
            self.check_button.grid()
            self.show_button.grid_remove()
            self.translation_label.grid_remove()
        self.show_next_word()
        
    def on_category_select(self, event):
        self.show_next_word()
        
    def show_next_word(self):
        if not self.words_data:
            return
            
        if self.mode_var.get() == "study":
            # В режиме изучения показываем слова по порядку
            self.current_category = self.category_var.get()
            if not self.current_category:
                return
                
            # Получаем список слов для текущей категории
            category_words = self.words_data[self.current_category]
            if not category_words:
                return
                
            # Преобразуем словарь в список пар (японское слово, данные)
            words_list = list(category_words.items())
            
            if self.current_word_index >= len(words_list):
                self.current_word_index = 0
            
            japanese_word, word_data = words_list[self.current_word_index]
            self.current_word = (japanese_word, word_data)
            self.current_word_index += 1
            
            self.japanese_label.config(text=japanese_word)
            self.romaji_label.config(text=word_data['romaji'])
            if self.mode_var.get() == "study":
                self.translation_label.config(text=word_data['russian'])
            else:
                self.translation_label.config(text="")
        else:
            # В режиме тестирования оставляем случайный выбор
            self.current_category = self.category_var.get()
            if not self.current_category:
                return
                
            category_words = self.words_data[self.current_category]
            if not category_words:
                return
                
            japanese_word = random.choice(list(category_words.keys()))
            self.current_word = (japanese_word, category_words[japanese_word])
            
            self.japanese_label.config(text=japanese_word)
            self.romaji_label.config(text=category_words[japanese_word]['romaji'])
            self.translation_label.config(text="")
            
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.focus()
        
    def show_translation(self):
        if hasattr(self, 'current_word'):
            self.translation_label.config(text=self.current_word[1]['russian'])
        
    def check_answer(self, event):
        if not hasattr(self, 'current_word'):
            return
            
        user_answer = self.answer_entry.get().strip().lower()
        correct_russian = self.current_word[1]['russian'].lower()
        
        # Проверяем только русский перевод
        if user_answer == correct_russian:
            self.correct_answers += 1
            self.translation_label.config(
                text=f"Правильно!\nЯпонский: {self.current_word[0]}\nРомадзи: {self.current_word[1]['romaji']}\nПеревод: {self.current_word[1]['russian']}", 
                foreground="green"
            )
        else:
            self.translation_label.config(
                text=f"Неправильно.\nПравильный ответ: {self.current_word[1]['russian']}\nРомадзи: {self.current_word[1]['romaji']}", 
                foreground="red"
            )
            
        self.total_questions += 1
        self.update_stats()
        
    def update_stats(self):
        stats_text = f"Правильных ответов: {self.correct_answers} из {self.total_questions}"
        if self.total_questions > 0:
            percentage = (self.correct_answers / self.total_questions) * 100
            stats_text += f" ({percentage:.1f}%)"
        self.stats_label.config(text=stats_text)
        
    def __del__(self):
        # Очистка временных файлов при закрытии программы
        pygame.mixer.quit()
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = JapaneseWordsApp(root)
    root.mainloop() 
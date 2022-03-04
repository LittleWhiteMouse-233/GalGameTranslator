# 妹汁翻译器
import tkinter as tk
from tkinter import scrolledtext

import myGUIWidget as mGW
import myLog
import shotsToString
import translationMain
import utils

FONT_SMALL = ('微软雅黑', 10)
FONT_MIDDLE = ('微软雅黑', 15)
FONT_BIG = ('微软雅黑', 20)
CONTENT_WIDTH = int(800 / FONT_SMALL[1])
BACKGROUND = "#FFFFFF"
PAD_X = 5
PAD_Y = 5


class FairyFoxTeaGUI(tk.Tk):
    Translator = translationMain.TranslationCore()
    S2S = shotsToString.Shots2String()
    logger = myLog.LoggerCreator.get_default_logger(name='FairyFoxTeaGUI')

    def __init__(self):
        super(FairyFoxTeaGUI, self).__init__()
        # 设置标题
        self.title('妹汁翻译器')
        # 设置宽高
        width = int(self.winfo_screenwidth() / 2)
        height = int(self.winfo_screenheight() / 2)
        self.geometry('%dx%d+%d+%d' % (width, height, int(width / 2), int(height / 2)))
        # 禁止修改宽高
        self.resizable(width=False, height=False)
        # 设置icon图标
        self.iconbitmap(utils.get_icon("FFT.png", in_resource=True))
        # 窗口背景
        self.config(background=BACKGROUND)
        # 狐仙茶
        photo = tk.PhotoImage(file=utils.get_resize_image("FairyFoxTea.png", height=height))
        fft = tk.Label(self, image=photo, bd=0)
        fft.image = photo
        fft.pack(side=tk.RIGHT)
        # 时钟
        text_time = tk.StringVar()
        tk.Label(fft, textvariable=text_time, font=FONT_MIDDLE, bd=0, bg=BACKGROUND) \
            .place(relx=0.4, rely=0.1)

        def get_time():
            text_time.set(utils.get_time())
            self.after(1000, get_time)

        get_time()
        # 退出按钮
        # tk.Button(self, text='退出', activebackground='#FF0000', command=self.quit).place(relx=0.95, rely=0.95)

        # 菜单
        main_menu = tk.Menu(self)
        menu = tk.Menu(main_menu, tearoff=False)
        menu.add_command(label='新建', command=self.add_new_shot, accelerator='Ctrl+N')
        self.bind('<Control-N>', self.add_new_shot)
        main_menu.add_cascade(label='镜头', menu=menu)
        self.config(menu=main_menu)

        # 主翻译区
        main_frame = mGW.TranslationFrame(self, label='主翻译区', font_label=FONT_MIDDLE, font_text=FONT_SMALL,
                                          text_width=CONTENT_WIDTH, text_height=10,
                                          pad_x=PAD_X, pad_y=PAD_Y, translator=self.Translator)
        self.mainFrame = main_frame
        main_frame.default_pack()

        # 功能区
        func_frame = tk.LabelFrame(self, text='功能区', font=FONT_MIDDLE)
        func_frame.pack(side=tk.TOP, fill=tk.X)
        # 功能输入框
        func_entry = tk.Entry(func_frame, font=FONT_SMALL, width=int(CONTENT_WIDTH / 2))
        func_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # 功能按钮区
        func_button_frame = tk.Frame(func_frame)
        func_button_frame.pack(side=tk.LEFT)

        # 翻译
        # tk.Button(frameFunction, text='翻译', command=translate).pack()
        # 去除下划线
        tk.Button(func_button_frame, text='去除间隔', command=lambda: main_frame.remove_seq(func_entry.get())). \
            grid(row=0, column=0, padx=PAD_X, pady=PAD_Y)
        # 清空输入
        tk.Button(func_button_frame, text='清空输入', command=main_frame.clear_text). \
            grid(row=0, column=1, padx=PAD_X, pady=PAD_Y)
        # 同步滚动
        button_sync = tk.Button(func_button_frame, text='同步滚动',
                                bg='#00FF00' if main_frame.SYNC_FLAG else '#FF0000')
        button_sync.grid(row=0, column=2, padx=PAD_X, pady=PAD_Y)

        def button_sync_func():
            main_frame.sync_text()
            if main_frame.SYNC_FLAG:
                button_sync.config(bg='#00FF00')
            else:
                button_sync.config(bg='#FF0000')

        button_sync.config(command=button_sync_func)
        # 交换位置
        tk.Button(func_button_frame, text='交换位置', command=main_frame.exchange_text). \
            grid(row=0, column=3, padx=PAD_X, pady=PAD_Y)

        # 副翻译区
        deputy_frame = tk.LabelFrame(self, text='副翻译区', font=FONT_MIDDLE)
        deputy_frame.pack(side=tk.TOP, fill=tk.X)
        self.deputyList = []
        deputy_count = 3

        def event_filter(event):
            if event.state == 12 and (event.keysym == 'c' or event.keysym == 'a'):
                return
            else:
                return 'break'

        for i in range(deputy_count):
            deputy_frame.columnconfigure(i, weight=1)
            di = scrolledtext.ScrolledText(deputy_frame, font=FONT_SMALL, width=int(CONTENT_WIDTH / (deputy_count + 1)),
                                           height=2)
            do = scrolledtext.ScrolledText(deputy_frame, font=FONT_SMALL, width=int(CONTENT_WIDTH / (deputy_count + 1)),
                                           height=2)
            do.bind('<Key>', lambda e: event_filter(e))
            self.deputyList.append((di, do))
            di.grid(row=0, column=i, padx=PAD_X, pady=PAD_Y, sticky=tk.EW)
            do.grid(row=1, column=i, padx=PAD_X, pady=PAD_Y, sticky=tk.EW)

        # 重设窗口退出方法
        self.protocol('WM_DELETE_WINDOW', self.default_quit)

    def add_new_shot(self):
        mGW.ShotWindow(self)
        self.iconify()

    def default_mainloop(self):
        self.logger.info("FairyFoxTeaGUI starting ...")
        self.translate_register()
        self.S2S.start_s2s()
        self.Translator.start_translate()
        self.logger.info("FairyFoxTeaGUI created.")
        self.mainloop()

    def default_quit(self):
        self.logger.info("FairyFoxTeaGUI quiting ...")
        self.Translator.shutdown_translate()
        self.S2S.shutdown_s2s()
        self.quit()
        self.destroy()
        self.logger.info("FairyFoxTeaGUI destroyed.")

    def translate_register(self):
        for ii, oo in self.deputyList:
            task = mGW.FrameTranslateTask(ii,
                                          self.mainFrame.cboxDict['from'],
                                          self.mainFrame.cboxDict['to'],
                                          self.mainFrame.cboxDict['by'],
                                          oo, self.Translator)
            self.Translator.add_translate_task(task)


# 主事件循环
if __name__ == '__main__':
    Lovely = FairyFoxTeaGUI()
    Lovely.default_mainloop()

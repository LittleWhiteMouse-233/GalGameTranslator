import tkinter as tk
from tkinter import ttk
from typing import Optional

import utils
from shotsToString import Shots2String, ShotToStringTask
from translationMain import TranslationCore, TranslationTask


class FrameTranslateTask(TranslationTask):

    def __init__(self, input_: tk.Text, from_: ttk.Combobox, to: ttk.Combobox, use: ttk.Combobox, output: tk.Text,
                 translator: TranslationCore):
        super(FrameTranslateTask, self).__init__()
        self.input_ = input_
        self.from_ = from_
        self.to = to
        self.use = use
        self.output = output
        self.translator = translator

    def get_input_from_to_use(self):
        return (
            self.input_.get('1.0', tk.END),
            self.from_.get(),
            self.to.get(),
            self.use.get()
        )

    def after_translate(self, change, pkg):
        use = self.use.get()
        use_ed = pkg[3]
        if use != use_ed:
            self.output.insert('1.0', "（控件提供的 by 或其对应方法不存在，以下翻译使用 %s 方法翻译）\n" % use_ed)
        if self.from_.get() != pkg[1]:
            self.output.insert('1.0', "（控件提供的 from 不存在，以下翻译将输入视为 %s 进行翻译）\n" % pkg[1])
        if self.to.get() != pkg[2]:
            self.output.insert('1.0', "（控件提供的 to 不存在，以下翻译将输出视为 %s 进行翻译）\n" % pkg[2])
        if change[3] and use == use_ed:
            # use值变化
            self.use.current(list(self.use['value']).index(use_ed))
            self.from_['value'] = self.translator.use_dict[use_ed]['from']
            self.from_.current(list(self.from_['value']).index(pkg[1]))
            self.to['value'] = self.translator.use_dict[use_ed]['to']
            self.to.current(list(self.to['value']).index(pkg[2]))

    def set_output(self, pkg):
        query_ed = pkg[0]
        if query_ed is None:
            self.set_out_all("(＠_＠;)：我不懂你在说什么呀？")
        elif query_ed == '':
            self.set_out_all("o( =•ω•= )m：你还什么都没说呢~")
        else:
            self.set_out_all(query_ed)

    def set_out_all(self, text):
        self.output.delete('1.0', tk.END)
        self.output.insert(tk.INSERT, text)


class TranslationFrame(tk.LabelFrame):
    """翻译框架"""
    SYNC_FLAG = False

    def __init__(self, root, *, label: str = '翻译', font_label: tuple, font_text: tuple,
                 text_width: int, text_height: int, pad_x=5, pad_y=5, input_activate=True,
                 translator: TranslationCore, task_id: int = None):
        super(TranslationFrame, self).__init__(root, text=label, font=font_label)
        self.translator = translator
        self.task_id = task_id
        # 主输入框
        iframe = tk.Frame(self)
        iframe.pack(fill=tk.BOTH, expand=True, padx=pad_x, pady=pad_y)
        self.inputScr = tk.Scrollbar(iframe)
        self.inputScr.pack(side=tk.RIGHT, fill=tk.Y)
        self.inputText = tk.Text(iframe, font=font_text, width=text_width, height=text_height, wrap='word')
        self.inputText.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        if not input_activate:
            self.inputText.bind('<Key>', lambda e: self.event_filter(e))
        self.inputText.config(yscrollcommand=self.inputScr.set)
        self.inputScr.config(command=self.inputText.yview)
        # 翻译选项
        cframe = tk.Frame(self)
        cframe.pack()
        self.cboxDict = dict()
        for i, s in enumerate(['from', 'by', 'to']):
            cbox = ttk.Combobox(cframe)
            cbox['value'] = tuple(self.translator.init_dict[s])
            cbox.current(0)
            cbox['state'] = 'readonly'
            tk.Label(cframe, text=s[0].upper() + s[1:] + ': ', font=font_text).grid(row=0, column=i * 2)
            cbox.grid(row=0, column=i * 2 + 1, padx=pad_x, pady=pad_y)
            self.cboxDict[s] = cbox
        # 主输出框
        oframe = tk.Frame(self)
        oframe.pack(fill=tk.BOTH, expand=True, padx=pad_x, pady=pad_y)
        self.outputScr = tk.Scrollbar(oframe)
        self.outputScr.pack(side=tk.RIGHT, fill=tk.Y)
        self.outputText = tk.Text(oframe, font=font_text, width=text_width, height=10, wrap='word')
        self.outputText.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.outputText.bind('<Key>', lambda e: self.event_filter(e))
        self.outputText.config(yscrollcommand=self.outputScr.set)
        self.outputScr.config(command=self.outputText.yview)

    def translate_register(self):
        """注册翻译任务"""
        trans_task = FrameTranslateTask(self.inputText,
                                        self.cboxDict['from'],
                                        self.cboxDict['to'],
                                        self.cboxDict['by'],
                                        self.outputText,
                                        self.translator)
        trans_task.set_output(('',))
        result = self.translator.add_translate_task(trans_task)
        if result is not False:
            if self.task_id is None:
                self.task_id = result
        else:
            self.task_id = None

    def translate_logout(self):
        """注销翻译任务"""
        if self.task_id is not None:
            self.translator.remove_translate_task(self.task_id)

    def check_exist(self):
        """检查任务是否存在"""
        if self.task_id is not None:
            c = self.translator.check_task_exist(self.task_id)
        else:
            return False
        if not c:
            self.task_id = None
        return c

    def default_pack(self):
        """自定义默认pack"""
        self.translate_register()
        self.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def get_in_all(self):
        """获取输入文本框的所有内容"""
        return self.inputText.get('1.0', tk.END)

    def get_out_all(self):
        """获取输出文本框的所有内容"""
        return self.outputText.get('1.0', tk.END)

    def set_in_all(self, text: str):
        """重置输入文本框的内容"""
        self.inputText.delete('1.0', tk.END)
        self.inputText.insert(tk.INSERT, text)

    def set_out_all(self, text: str):
        """重置输出文本框的内容"""
        self.outputText.delete('1.0', tk.END)
        self.outputText.insert(tk.INSERT, text)

    @staticmethod
    def event_filter(event):
        """事件过滤器"""
        if event.state == 12 and (event.keysym == 'c' or event.keysym == 'a'):
            return
        else:
            return 'break'

    def clear_text(self):
        """清空文本"""
        self.inputText.delete('1.0', tk.END)
        self.outputText.delete('1.0', tk.END)

    def remove_seq(self, seq: str):
        """移除指定间隔字符"""
        s = self.inputText.get('1.0', tk.END)
        self.clear_text()
        self.inputText.insert('1.0', utils.remove_char(s, seq))

    def sync_text(self, state: bool = None) -> bool:
        """同步文本"""
        if state is not None:
            self.SYNC_FLAG = state
        else:
            self.SYNC_FLAG = ~ self.SYNC_FLAG

        def sync_set(*args):
            self.inputScr.set(*args)
            self.outputScr.set(*args)
            self.inputText.yview('moveto', self.inputScr.get()[0])
            self.outputText.yview('moveto', self.outputScr.get()[0])

        if self.SYNC_FLAG:
            self.inputText.config(yscrollcommand=sync_set)
            self.outputText.config(yscrollcommand=sync_set)
        else:
            self.inputText.config(yscrollcommand=self.inputScr.set)
            self.outputText.config(yscrollcommand=self.outputScr.set)
        return self.SYNC_FLAG

    def exchange_text(self):
        """交换输入文本框和输出文本框的内容以及"""
        si = self.get_in_all()
        so = self.get_out_all()
        self.clear_text()
        self.set_in_all(so)
        self.set_out_all(si)
        cf = self.cboxDict['from'].get()
        ct = self.cboxDict['to'].get()
        if ct in self.cboxDict['from']['value']:
            self.cboxDict['from'].current(self.cboxDict['from']['value'].index(ct))
        else:
            self.cboxDict['from'].current(0)
        if cf in self.cboxDict['to']['value']:
            self.cboxDict['to'].current(self.cboxDict['to']['value'].index(cf))
        else:
            self.cboxDict['to'].current(0)


class S2STask(ShotToStringTask):
    def __init__(self, bbox: Optional[tuple[int, int, int, int]], lang: Optional[str], output: tk.Text = None):
        super(S2STask, self).__init__()
        self.bbox = bbox
        self.lang = lang
        self.content = ''
        self.output = output

    def get_bbox_lang(self):
        return self.bbox, self.lang

    def set_content(self, text):
        self.content = text
        if self.output is not None:
            self.format_content()
            self.output.delete('1.0', tk.END)
            self.output.insert(tk.INSERT, self.content)

    def format_content(self):
        self.content = self.content.replace('\n', ' ')


class ShotWindow(tk.Toplevel):
    """监控镜头快照窗口"""
    TRANSPARENT_COLOR = 'gray'
    result_window = None

    def __init__(self, root, *, shot_id: int = None):
        super(ShotWindow, self).__init__(root)
        self.root = root
        self.logger = root.logger
        self.s2s: Shots2String = root.S2S
        self.shot_id = shot_id
        self.shot_preregister()
        self.title('ShotWindow-' + str(shot_id))
        self.iconbitmap(utils.get_icon("FFT.png"))
        self.geometry('%dx%d+%d+%d' % (int(self.winfo_screenwidth() / 4), int(self.winfo_screenwidth() / 4),
                                       int(self.winfo_screenwidth() / 4), int(self.winfo_screenwidth() / 4)))
        menu = tk.Menu(self)
        menu.add_command(label='锁定', command=self.command_lock)
        self.config(menu=menu)
        self.attributes('-topmost', True)
        self.focus()
        # 检测语言下拉选择框
        cframe = tk.Frame(self)
        cframe.pack()
        tk.Label(cframe, text='检测文本：').grid(row=0, column=0)
        self.cbox = ttk.Combobox(cframe)
        self.cbox['value'] = tuple(self.s2s.lang_dict.keys())
        self.cbox.current(0)
        self.cbox['state'] = 'readonly'
        self.cbox.grid(row=0, column=1)
        # 设置透明色，使用该颜色填充的控件可以直接穿透
        self.wm_attributes('-transparentcolor', 'gray')
        # self.config(bg=self.TRANSPARENT_COLOR)
        self.Canvas = tk.Canvas(self)
        self.Canvas.pack(fill=tk.BOTH, expand=True)
        self.update()
        self.Canvas.create_rectangle(0, 0, self.winfo_width(), self.winfo_height(),
                                     fill=self.TRANSPARENT_COLOR, outline=self.TRANSPARENT_COLOR)
        self.bind('<Configure>', self.on_resize)
        # 重设窗口退出方法
        self.protocol('WM_DELETE_WINDOW', self.default_quit)
        self.logger.info('ShotWindow-' + str(self.shot_id) + ": Created.")

    def default_quit(self):
        """自定义默认quit"""
        if self.result_window is not None:
            if not self.result_window.exiting:
                self.result_window.command_unlock()
            self.after(1000, self.default_quit())
        else:
            self.destroy()
            self.logger.info('ShotWindow-' + str(self.shot_id) + ": Destroyed.")

    def shot_preregister(self):
        """预注册窗口"""
        result = self.s2s.add_shot(S2STask(None, None, None), self.shot_id)
        if result is not False:
            if self.shot_id is None:
                self.shot_id = result
        else:
            self.shot_id = None
            self.logger.error("Preregister shot_id %s failed.", str(self.shot_id))

    def command_lock(self):
        """锁定命令"""
        if self.shot_id is None:
            self.shot_preregister()
        if self.shot_id is None:
            self.logger.error("Lock failed.")
            return
        self.withdraw()
        self.update()
        bbox = (self.winfo_x(), self.winfo_y(),
                self.winfo_x() + self.winfo_width(), self.winfo_y() + self.winfo_height())
        self.result_window = ShotResultWindow(self, bbox, self.cbox.get())

    def on_resize(self, _):
        """实时更新画布透明矩形的尺寸"""
        self.update()
        self.Canvas.delete(tk.ALL)
        self.Canvas.create_rectangle(0, 0, self.winfo_width(), self.winfo_height(),
                                     fill=self.TRANSPARENT_COLOR, outline=self.TRANSPARENT_COLOR)


class ShotResultWindow(tk.Toplevel):
    """监控镜头反馈窗口"""
    FONT = ('微软雅黑', 10)
    exiting = False

    def __init__(self, root: ShotWindow, bbox: tuple[int, int, int, int], lang: str):
        super(ShotResultWindow, self).__init__(root)
        self.root = root
        self.logger = root.logger
        self.shot_id = root.shot_id
        self.translator: TranslationCore = root.root.Translator
        self.s2s: Shots2String = root.s2s
        self.iconbitmap(utils.get_icon("FFT.png"))
        self.geometry('%dx%d+%d+%d' % (root.winfo_width(),
                                       root.winfo_height(),
                                       root.winfo_width() + root.winfo_x(),
                                       root.winfo_y()))
        self.update()
        menu = tk.Menu(self)
        menu.add_command(label='解锁', command=self.command_unlock)
        self.config(menu=menu)
        self.attributes('-topmost', True)
        self.TF = TranslationFrame(self, font_label=self.FONT, font_text=self.FONT,
                                   text_width=int(self.winfo_width() / self.FONT[1]), text_height=1,
                                   input_activate=False, translator=self.translator)
        self.TF.default_pack()
        # 更新窗口
        self.s2s.update_shot(S2STask(bbox, lang, self.TF.inputText), self.shot_id)
        self.title('ShotResult-' + str(self.shot_id) + '-' + lang)
        # 重设窗口退出方法
        self.protocol('WM_DELETE_WINDOW', self.command_unlock)
        self.logger.info('ShotResult-' + str(self.shot_id) + ": Created.")

    def default_quit(self):
        """自定义默认quit"""
        if self.check_exist():
            self.after(1000, self.default_quit)
        else:
            self.root.deiconify()
            self.root.update()
            self.root.shot_id = None
            self.root.result_window = None
            self.destroy()
            self.logger.info('ShotResult-' + str(self.shot_id) + ": Destroyed.")

    def check_exist(self):
        """检查任务是否存在"""
        ct = self.TF.check_exist()
        if self.shot_id is not None:
            cs = self.s2s.check_shot_exist(self.shot_id)
        else:
            return ct
        if not cs:
            self.shot_id = None
        return ct or cs

    def command_unlock(self):
        """解锁命令"""
        self.exiting = True
        # 注销翻译任务
        self.TF.translate_logout()
        # 注销窗口
        if self.shot_id is not None:
            self.s2s.remove_shot(self.shot_id)
        self.default_quit()

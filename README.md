# NoteGod - Python Floating Desktop Note & Voice Assistant

**NoteGod** เป็นแอปพลิเคชันโน้ตและผู้ช่วยอัดเสียงระดับพรีเมียม พัฒนาด้วย **Python (PySide6 / Qt6)** ดีไซน์รูปแบบ **Desktop Floating Widget** และ **Dark Glassmorphic UI**

## 🌟 ฟีเจอร์หลัก (Key Features)

1. **Floating Desktop Widget (`floating_widget.py`)**:
   - โน้ตลอยแบบไร้ขอบ (`Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint`) ลอยอยู่บนหน้าจอ Windows
   - สามารถกดคลิกลากย้ายตำแหน่งไปได้ทั่วหน้าจอ Desktop
   - คลิกเพื่อเปิด/ซ่อนหน้าต่างหลักของ NoteGod

2. **Sidebar ประวัติโน้ต (`sidebar_widget.py`)**:
   - รายการโน้ตสไตล์ AI Chat History พร้อมช่องค้นหาข้อความแบบเรียลไทม์
   - แสดงสถานะโน้ตที่มีรูปภาพ 🖼️ และเสียงบันทึก 🎙️

3. **ระบบจัดวางรูปภาพ & พรีวิว Lightbox (`note_editor.py` & `lightbox.py`)**:
   - สลับวางรูปภาพให้อยู่ **ด้านบนข้อความ** หรือ **ด้านล่างข้อความ** เพื่อความสบายตาในการอ่าน
   - แสดงรูปเป็น Thumbnail ขนาดเล็ก เมื่อกดคลิกจะขยายภาพใหญ่ (Lightbox Modal)

4. **เครื่องมือบันทึกเสียงและฟังเสียงสด (`audio_engine.py`)**:
   - อัดเสียงสดจากไมโครโฟน เก็บไฟล์เสียง `.wav`
   - เครื่องเล่นเสียงบันทึก (Audio Player) ย้อนหลัง

5. **แท็บถอดเสียง & AI สรุปสาระสำคัญ (`transcript_view.py`)**:
   - **แท็บ 1 (โน้ต & สื่อ)**: บันทึกข้อความ แนบรูปภาพ อัดเสียงสด
   - **แท็บ 2 (ถอดเสียง & สรุป)**: แสดงบทถอดเสียงจากการประชุม (Speech-to-Text) และสรุปประเด็นสำคัญ (AI Summary)

---

## 🚀 วิธีการติดตั้งและรันใช้งาน

1. ติดตั้งไลบรารีที่จำเป็น:
```bash
pip install PySide6 SpeechRecognition sounddevice soundfile
```

2. รันแอปพลิเคชัน:
```bash
python main.py
```

import json
import os
import time
import uuid

DATA_DIR = os.path.join(os.path.expanduser("~"), ".notegod")
NOTES_FILE = os.path.join(DATA_DIR, "notes.json")
MEDIA_DIR = os.path.join(DATA_DIR, "media")

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MEDIA_DIR, exist_ok=True)

class NoteDatabase:
    def __init__(self):
        ensure_dirs()
        self.notes = self.load_notes()
        if not self.notes:
            self.create_sample_notes()

    def load_notes(self):
        if os.path.exists(NOTES_FILE):
            try:
                with open(NOTES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("Error loading notes:", e)
                return []
        return []

    def save_notes(self):
        ensure_dirs()
        try:
            with open(NOTES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error saving notes:", e)

    def get_all_notes(self):
        return sorted(self.notes, key=lambda x: x.get("updated_at", 0), reverse=True)

    def get_note_by_id(self, note_id):
        for n in self.notes:
            if n.get("id") == note_id:
                return n
        return None

    def add_or_update_note(self, note_data):
        if not note_data.get("id"):
            note_data["id"] = str(uuid.uuid4())
            note_data["created_at"] = time.time()
        
        note_data["updated_at"] = time.time()

        # Ensure required fields exist
        note_data.setdefault("title", "โน้ตไม่มีชื่อ")
        note_data.setdefault("content", "")
        note_data.setdefault("images", [])
        note_data.setdefault("image_position", "inline")
        note_data.setdefault("audio_path", "")
        note_data.setdefault("audio_duration", 0)
        note_data.setdefault("audio_files", [])

        # Convert legacy audio_path if audio_files is empty
        if note_data.get("audio_path") and not note_data.get("audio_files"):
            note_data["audio_files"] = [{
                "path": note_data["audio_path"],
                "duration": note_data.get("audio_duration", 0),
                "name": "เสียงบันทึก #1"
            }]
        note_data.setdefault("summary", "")
        note_data.setdefault("tags", ["General"])

        idx = next((i for i, n in enumerate(self.notes) if n.get("id") == note_data["id"]), -1)
        if idx >= 0:
            self.notes[idx] = note_data
        else:
            self.notes.insert(0, note_data)

        self.save_notes()
        return note_data

    def delete_note(self, note_id):
        self.notes = [n for n in self.notes if n.get("id") != note_id]
        self.save_notes()

    def create_sample_notes(self):
        sample_1 = {
            "id": "sample-1",
            "title": "📌 การประชุมวางแผนยุทธศาสตร์ AI 2026",
            "content": "สรุปประเด็นหลักจากการประชุมทีมพัฒนาผลิตภัณฑ์:\n\n1. ฟีเจอร์ Floating Note ต้องใช้งานง่าย ลากไปตำแหน่งใดก็ได้บน Desktop\n2. โครงสร้างโน้ตต้องรองรับข้อความ รูปภาพ (ขนาดเล็ก กดขยายได้) และเสียงบันทึก\n3. ตำแหน่งรูปภาพเลือกให้อยู่ด้านบนหรือด้านล่างของข้อความเพื่อให้อ่านสะดวก\n4. ระบบถอดเสียง (Audio Transcription) แยกออกเป็นอีกแท็บเพื่อเปิดอ่านได้ง่าย",
            "images": [],
            "image_position": "bottom",
            "audio_path": "",
            "audio_duration": 45,
            "transcript": "[00:00] ประธานเปิดการประชุมวางแผน AI NoteGod\n[00:12] อภิปรายเรื่อง UX/UI ของ Floating Note บนหน้าจอ\n[00:25] สรุปให้รูปภาพแสดงเป็น Thumbnail เล็กๆ เมื่อคลิกจะขยายภาพใหญ่ Lightbox\n[00:38] ปิดการประชุมและกำหนดเส้นส่งมอบงาน",
            "summary": "🎯 **สรุปสาระสำคัญจากการประชุม:**\n- มุ่งเน้นความสะดวกในการใช้งานบน Desktop ด้วย Floating Widget\n- การจัดวางรูปภาพคงที่ที่ด้านบนหรือล่าง เพื่อป้องกันข้อความสับสน\n- แยกแท็บถอดเสียงจากการประชุมเพื่อเปิดอ่านเฉพาะข้อมูลบทสนทนา",
            "tags": ["Meeting", "Work"],
            "created_at": time.time() - 3600,
            "updated_at": time.time() - 3600
        }

        sample_2 = {
            "id": "sample-2",
            "title": "💡 ไอเดียและบันทึกย่อประจำวัน",
            "content": "รายการที่ต้องทำวันนี้:\n- [x] ออกแบบโครงสร้าง PySide6 GUI\n- [x] เพิ่มระบบบันทึกเสียงและฟังเสียง\n- [ ] ทดสอบระบบถอดเสียงภาษาไทยและภาษาอังกฤษ",
            "images": [],
            "image_position": "top",
            "audio_path": "",
            "audio_duration": 0,
            "transcript": "",
            "summary": "",
            "tags": ["Idea"],
            "created_at": time.time() - 86400,
            "updated_at": time.time() - 86400
        }

        self.notes = [sample_1, sample_2]
        self.save_notes()

from flask import Flask, render_template, request, session, redirect, url_for
import random
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # ใช้เซสชัน

# ข้อมูลคำและภาพที่ใช้ในเกม
word_image_pairs = [
    {"word": "Dog", "image": "dog.gif"},
    {"word": "Cat", "image": "cat.gif"},
    {"word": "Car", "image": "car.gif"},
    {"word": "Bird", "image": "bird.gif"},
]

# ฟังก์ชันเชื่อมต่อฐานข้อมูล
def get_db_connection():
    conn = sqlite3.connect('game.db')
    conn.row_factory = sqlite3.Row  # จะได้ข้อมูลเป็น dictionary
    return conn

# ฟังก์ชันสร้างตาราง used_images และ game_history (หากยังไม่มี)
def create_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS used_images (image TEXT)')
    conn.execute('''CREATE TABLE IF NOT EXISTS game_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        score INTEGER,
                        date TEXT)''')  # ตารางสำหรับบันทึกประวัติการเล่น
    conn.commit()
    conn.close()

create_db()

# หน้า Home
@app.route('/')
def home():
    # รีเซ็ตคะแนนก่อนเริ่มเกม
    session['score'] = 0  # เซ็ตคะแนนให้เป็น 0
    # ลบข้อมูลที่เคยใช้ไปในฐานข้อมูล
    conn = get_db_connection()
    conn.execute('DELETE FROM used_images')  # ลบข้อมูลภาพที่เคยใช้
    conn.commit()
    conn.close()
    return render_template('home.html')  # ไปที่หน้า home.html

# หน้าเครดิต
@app.route('/credit')
def credit():
    return render_template('credit.html')  # ไปที่หน้า credit.html

# หน้าเกม
@app.route('/start_game')
def start_game():
    # กำหนดคะแนนเริ่มต้นเป็น 0 ถ้าไม่เคยมีการเริ่มเกม
    if 'score' not in session:
        session['score'] = 0

    # เชื่อมต่อฐานข้อมูล
    conn = get_db_connection()
    # ดึงข้อมูลภาพที่ทายถูกแล้วจากฐานข้อมูล
    used_images_query = conn.execute('SELECT image FROM used_images').fetchall()
    used_images = [row['image'] for row in used_images_query]
    conn.close()

    # เลือกรูปที่ยังไม่ถูกใช้
    available_pairs = [pair for pair in word_image_pairs if pair["image"] not in used_images]

    # ถ้าทายครบหมดแล้ว
    if not available_pairs:
        return redirect(url_for('win'))  # ไปที่หน้า "You Win!"

    # เลือกรูปภาพที่ยังไม่ถูกทาย
    random_pair = random.choice(available_pairs)

    # ส่งข้อมูลไปยัง index.html
    return render_template('index.html', image=random_pair["image"], word=random_pair["word"], result=None, score=session['score'])

# ตรวจสอบคำตอบ
@app.route('/check_answer', methods=['POST'])
def check_answer():
    if 'user_answer' not in request.form or 'correct_answer' not in request.form or 'image' not in request.form:
        return redirect(url_for('home'))  # ถ้าไม่มีคีย์เหล่านี้ ให้ไปที่หน้าแรกใหม่

    user_answer = request.form['user_answer']
    correct_answer = request.form['correct_answer']
    image = request.form['image']

    # ตรวจสอบคำตอบ
    if user_answer.strip().lower() == correct_answer.strip().lower():
        # ถ้าทายถูก จะเพิ่มภาพที่ถูกใช้ไปในฐานข้อมูล
        conn = get_db_connection()
        conn.execute('INSERT INTO used_images (image) VALUES (?)', (image,))
        conn.commit()
        conn.close()

        # เพิ่มคะแนน
        session['score'] += 1
        result = "Correct!"  # แต่จะไม่แสดงผลใน HTML
    else:
        # หากทายผิด
        result = "Incorrect Answer!"  # แสดงข้อความทายผิด

    # ส่งผลลัพธ์ไปยังหน้า lose.html หรือแสดงภาพถัดไป
    if result == "Incorrect Answer!":
        user_answer_display = user_answer
        return render_template('lose.html', result=result, user_answer=user_answer_display, correct_answer=correct_answer, image=image, score=session['score'])  # ส่งคะแนนไปยัง lose.html
    else:
        return redirect(url_for('start_game'))  # แสดงภาพถัดไป

# ปุ่มรีสตาร์ทเกม
@app.route('/restart')
def restart():
    # รีเซ็ตฐานข้อมูลและคะแนน
    conn = get_db_connection()
    conn.execute('DELETE FROM used_images')
    conn.commit()
    conn.close()

    # รีเซ็ตคะแนนในเซสชัน
    session['score'] = 0
    return redirect(url_for('start_game'))

# หน้า "You Win!"
@app.route('/win')
def win():
    # บันทึกคะแนนและวันที่ลงในฐานข้อมูล
    score = session.get('score', 0)
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    conn.execute('INSERT INTO game_history (score, date) VALUES (?, ?)', (score, date))
    conn.commit()
    conn.close()

    return render_template('win.html', score=score)  # ไปที่หน้า win.html

# หน้า career (ประวัติการเล่น)
@app.route('/history')
def career():
    # ดึงข้อมูลประวัติการเล่นจากฐานข้อมูล
    conn = get_db_connection()
    game_history_query = conn.execute('SELECT score, date FROM game_history ORDER BY date DESC').fetchall()
    conn.close()

    # ส่งข้อมูลไปยัง career.html
    return render_template('career.html', game_history=game_history_query)

# ฟังก์ชันรีเซ็ตข้อมูลการเล่น
@app.route('/reset_career', methods=['POST'])
def reset_career():
    conn = get_db_connection()
    conn.execute('DELETE FROM game_history')  # ลบข้อมูลในตาราง game_history
    conn.commit()
    conn.close()

    return redirect(url_for('career'))  # รีไดเรกต์ไปที่หน้า career.html

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from config import Config
import json

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Добавьте в main.py словарь переводов
FLOWER_NAMES = {
    'peony': 'Пионы',
    'tulip': 'Тюльпаны',
    'alstroemeria': 'Альстромерии',
    'chrysanthemum': 'Хризантемы',
    'lily': 'Лилии'
}


# Добавьте в контекст шаблонов
@app.context_processor
def utility_processor():
    def get_flower_name_ru(flower_type):
        return FLOWER_NAMES.get(flower_type, flower_type)

    return dict(
        get_time_remaining=get_time_remaining,
        get_flower_name_ru=get_flower_name_ru,
        FLOWER_NAMES=FLOWER_NAMES
    )

# Модели базы данных
class Flower(db.Model):
    __tablename__ = 'flowers'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # peony, tulip, alstroemeria, chrysanthemum, lily
    vase_id = db.Column(db.Integer, default=None)  # 1, 2, 3 или None
    status = db.Column(db.String(20), default='new')  # 'new', 'trimmed', 'expired'
    trimmed_at = db.Column(db.DateTime, nullable=True)
    water_changed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    def __init__(self, flower_type, vase_id=None):
        self.type = flower_type
        self.vase_id = vase_id
        self.status = 'new'
        # Устанавливаем срок жизни для каждого типа цветов (в днях)
        life_days = {
            'peony': 5,
            'tulip': 7,
            'alstroemeria': 10,
            'chrysanthemum': 14,
            'lily': 8
        }
        self.expires_at = datetime.utcnow() + timedelta(days=life_days.get(flower_type, 7))


# Функция для расчета оставшегося времени
def get_time_remaining(target_time):
    if not target_time:
        return "Нет данных"

    now = datetime.utcnow()
    if now >= target_time:
        return "Время истекло"

    diff = target_time - now
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60

    if days > 0:
        return f"{days}д {hours}ч"
    else:
        return f"{hours}ч {minutes}м"


# Добавляем функцию в контекст шаблонов
@app.context_processor
def utility_processor():
    return dict(get_time_remaining=get_time_remaining)


# Главная страница (сайт только для девушки)
@app.route('/')
def garden():
    # Получаем все активные цветы (не истекшие)
    active_flowers = Flower.query.filter(
        Flower.expires_at > datetime.utcnow(),
        Flower.status != 'expired'
    ).all()

    # Группируем цветы по вазам
    vases = {1: [], 2: [], 3: []}

    for flower in active_flowers:
        if flower.vase_id and flower.vase_id in vases:
            vases[flower.vase_id].append(flower)

    # Подготавливаем данные для отображения
    vases_data = []
    for vase_id in [1, 2, 3]:
        flowers_in_vase = vases[vase_id]
        vase_data = {
            'id': vase_id,
            'flowers': flowers_in_vase,
            'has_flowers': len(flowers_in_vase) > 0,
            'needs_water': False,
            'next_water_change': None
        }

        # Проверяем, нужно ли менять воду
        if flowers_in_vase:
            # Находим самое раннее время смены воды среди цветов в вазе
            water_times = []
            for f in flowers_in_vase:
                if f.status == 'trimmed':
                    if f.water_changed_at:
                        water_times.append(f.water_changed_at)
                    elif f.trimmed_at:
                        water_times.append(f.trimmed_at)
                    else:
                        water_times.append(f.created_at)

            if water_times:
                next_water = min(water_times) + timedelta(hours=24)
                vase_data['next_water_change'] = next_water
                vase_data['needs_water'] = datetime.utcnow() >= next_water

        vases_data.append(vase_data)

    # Получаем неподрезанные цветы
    untrimmed_flowers = Flower.query.filter(
        Flower.status == 'new',
        Flower.expires_at > datetime.utcnow()
    ).all()

    # Проверяем, есть ли просроченные цветы для удаления
    expired_flowers = Flower.query.filter(
        Flower.expires_at <= datetime.utcnow(),
        Flower.status != 'expired'
    ).all()

    for flower in expired_flowers:
        flower.status = 'expired'
    if expired_flowers:
        db.session.commit()

    return render_template('garden.html',
                           vases=vases_data,
                           untrimmed_flowers=untrimmed_flowers,
                           now=datetime.utcnow())


# API эндпоинты для AJAX запросов
@app.route('/trim_flower', methods=['POST'])
def trim_flower():
    data = request.json
    flower_id = data.get('flower_id')
    vase_id = data.get('vase_id')

    flower = Flower.query.get(flower_id)
    if flower and flower.status == 'new':
        flower.status = 'trimmed'
        flower.trimmed_at = datetime.utcnow()
        flower.water_changed_at = datetime.utcnow()
        flower.vase_id = vase_id
        db.session.commit()
        return jsonify({'success': True})

    return jsonify({'success': False}), 400


@app.route('/change_water', methods=['POST'])
def change_water():
    data = request.json
    vase_id = data.get('vase_id')

    # Обновляем время смены воды для всех цветов в вазе
    flowers = Flower.query.filter_by(vase_id=vase_id, status='trimmed').all()
    for flower in flowers:
        flower.water_changed_at = datetime.utcnow()

    db.session.commit()
    return jsonify({'success': True})


@app.route('/add_flower', methods=['POST'])
def add_flower():
    data = request.json
    flower_type = data.get('type')

    if flower_type in ['peony', 'tulip', 'alstroemeria', 'chrysanthemum', 'lily']:
        new_flower = Flower(flower_type=flower_type)
        db.session.add(new_flower)
        db.session.commit()
        return jsonify({'success': True, 'flower_id': new_flower.id})

    return jsonify({'success': False}), 400


# Админская страница для добавления цветов
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        # Проверяем, это запрос на вход или добавление цветка
        if 'password' in request.form:
            password = request.form.get('password')
            if password == 'your_admin_password':  # Установите свой пароль
                session['admin'] = True
            else:
                return render_template('admin_login.html', error=True)

    if not session.get('admin'):
        return render_template('admin_login.html')

    if request.method == 'POST' and 'flower_type' in request.form:
        flower_type = request.form['flower_type']
        if flower_type in ['peony', 'tulip', 'alstroemeria', 'chrysanthemum', 'lily']:
            new_flower = Flower(flower_type=flower_type)
            db.session.add(new_flower)
            db.session.commit()

    # Получаем статистику для админки
    total_flowers = Flower.query.count()
    active_flowers = Flower.query.filter(
        Flower.expires_at > datetime.utcnow(),
        Flower.status != 'expired'
    ).count()
    flowers_in_vases = Flower.query.filter(
        Flower.vase_id.isnot(None),
        Flower.status == 'trimmed',
        Flower.expires_at > datetime.utcnow()
    ).count()

    return render_template('admin.html',
                           total_flowers=total_flowers,
                           active_flowers=active_flowers,
                           flowers_in_vases=flowers_in_vases)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
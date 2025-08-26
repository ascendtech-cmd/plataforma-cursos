from app import db, login
from flask_login import UserMixin
from passlib.hash import pbkdf2_sha256 as sha256
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(2), nullable=True)
    gender = db.Column(db.String(30), nullable=True)
    education_level = db.Column(db.String(50), nullable=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    courses = db.relationship('Enrollment', back_populates='student', cascade="all, delete-orphan")
    completed_lessons = db.relationship('LessonCompletion', backref='student', lazy='dynamic')
    quiz_attempts = db.relationship('QuizAttempt', backref='student', lazy='dynamic')
    lesson_responses = db.relationship('LessonResponse', backref='student', lazy='dynamic')
    authorizations = db.relationship('CourseAuthorization', back_populates='user', cascade="all, delete-orphan")

    def set_password(self, password): self.password_hash = sha256.hash(password)
    def check_password(self, password): return sha256.verify(password, self.password_hash)
    def __repr__(self): return f'<User {self.full_name}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    # CAMPO DE CARGA HORÁRIA ADICIONADO
    course_load = db.Column(db.Integer, nullable=False, server_default='0')
    
    modules = db.relationship('Module', backref='course', lazy='dynamic', cascade="all, delete-orphan")
    enrollments = db.relationship('Enrollment', back_populates='course', cascade="all, delete-orphan")
    authorized_users = db.relationship('CourseAuthorization', back_populates='course', cascade="all, delete-orphan")
    def __repr__(self): return f'<Course {self.title}>'

# ... (o resto do arquivo models.py permanece o mesmo) ...
class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False, server_default='1')
    lessons = db.relationship('Lesson', backref='module', lazy='dynamic', cascade="all, delete-orphan")
    quiz = db.relationship('Quiz', backref='module', uselist=False, cascade="all, delete-orphan")
    def __repr__(self): return f'<Module {self.title}>'
class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    content = db.Column(db.Text, nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    has_response_field = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    order = db.Column(db.Integer, nullable=False, server_default='1')
    completions = db.relationship('LessonCompletion', backref='lesson', lazy='dynamic', cascade="all, delete-orphan")
    attachments = db.relationship('LessonAttachment', backref='lesson', lazy='dynamic', cascade="all, delete-orphan")
    responses = db.relationship('LessonResponse', backref='lesson', lazy='dynamic', cascade="all, delete-orphan")
    def __repr__(self): return f'<Lesson {self.title}>'
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('User', back_populates='courses')
    course = db.relationship('Course', back_populates='enrollments')
    def __repr__(self): return f'<Enrollment user_id={self.user_id} course_id={self.course_id}>'
class LessonCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    completion_date = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self): return f'<LessonCompletion user_id={self.user_id} lesson_id={self.lesson_id}>'
class LessonAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    display_name = db.Column(db.String(200), nullable=False)
    attachment_type = db.Column(db.String(10), nullable=False)
    url_or_filename = db.Column(db.String(300), nullable=False)
    def __repr__(self): return f'<LessonAttachment {self.display_name}>'
class LessonResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    response_text = db.Column(db.Text, nullable=False)
    response_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    def __repr__(self): return f'<LessonResponse user_id={self.user_id} lesson_id={self.lesson_id}>'
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False, unique=True)
    questions = db.relationship('Question', backref='quiz', lazy='dynamic', cascade="all, delete-orphan")
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy='dynamic', cascade="all, delete-orphan")
    def __repr__(self): return f'<Quiz {self.title}>'
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    choices = db.relationship('Choice', backref='question', lazy='dynamic', cascade="all, delete-orphan")
    def __repr__(self): return f'<Question {self.text[:50]}>'
class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    def __repr__(self): return f'<Choice {self.text[:50]}>'
class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Float, nullable=False)
    attempt_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    def __repr__(self): return f'<QuizAttempt score={self.score}>'

class CourseAuthorization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    user = db.relationship('User', back_populates='authorizations')
    course = db.relationship('Course', back_populates='authorized_users')
    def __repr__(self): return f'<CourseAuthorization user_id={self.user_id} course_id={self.course_id}>'
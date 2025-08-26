from app import app, db
from flask import render_template, flash, redirect, url_for, request, make_response, abort, send_from_directory
from app.forms import (RegistrationForm, LoginForm, CourseForm, ModuleForm, 
                       LessonForm, QuestionForm, LinkForm, FileForm, LessonResponseForm, AuthorizeUserForm, ChangePasswordForm)
from app.models import (User, Course, Module, Lesson, Enrollment, LessonCompletion, 
                        Quiz, Question, Choice, QuizAttempt, LessonAttachment, LessonResponse, CourseAuthorization)
from flask_login import current_user, login_user, logout_user, login_required
from weasyprint import HTML
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import markdown
import pathlib

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Página Inicial')

# --- ROTAS DE ADMIN ---
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    return render_template('admin/dashboard.html', title='Painel do Administrador')

@app.route('/admin/courses')
@login_required
def manage_courses():
    if not current_user.is_admin:
        abort(403)
    page = request.args.get('page', 1, type=int)
    courses_pagination = Course.query.order_by(Course.title).paginate(page=page, per_page=10)
    return render_template('admin/courses_admin.html', title='Gerenciar Cursos', courses=courses_pagination)

@app.route('/admin/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        abort(403)
    page = request.args.get('page', 1, type=int)
    users_pagination = User.query.order_by(User.full_name).paginate(page=page, per_page=10)
    return render_template('admin/users.html', title='Gerenciar Usuários', users=users_pagination)

@app.route('/admin/promote_user/<int:user_id>', methods=['POST'])
@login_required
def promote_user(user_id):
    if not current_user.is_admin:
        abort(403)
    user_to_promote = User.query.get_or_404(user_id)
    user_to_promote.is_admin = True
    db.session.commit()
    flash(f'{user_to_promote.full_name} foi promovido a administrador.', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/demote_user/<int:user_id>', methods=['POST'])
@login_required
def demote_user(user_id):
    if not current_user.is_admin:
        abort(403)
    user_to_demote = User.query.get_or_404(user_id)
    if user_to_demote.id == current_user.id:
        flash('Você não pode remover suas próprias permissões de administrador.', 'danger')
        return redirect(url_for('manage_users'))
    user_to_demote.is_admin = False
    db.session.commit()
    flash(f'{user_to_demote.full_name} foi rebaixado para aluno.', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if not current_user.is_admin:
        abort(403)
    form = CourseForm()
    if form.validate_on_submit():
        new_course = Course(title=form.title.data, description=form.description.data, course_load=form.course_load.data)
        db.session.add(new_course)
        db.session.commit()
        flash('Curso adicionado com sucesso!')
        return redirect(url_for('manage_courses'))
    return render_template('admin/course_form.html', title='Adicionar Novo Curso', form=form, legend='Adicionar Novo Curso')

@app.route('/admin/edit_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    if not current_user.is_admin:
        abort(403)
    course = Course.query.get_or_404(course_id)
    form = CourseForm()
    if form.validate_on_submit():
        course.title = form.title.data
        course.description = form.description.data
        course.course_load = form.course_load.data
        db.session.commit()
        flash('Curso atualizado com sucesso!')
        return redirect(url_for('manage_courses'))
    elif request.method == 'GET':
        form.title.data = course.title
        form.description.data = course.description
        form.course_load.data = course.course_load
    return render_template('admin/course_form.html', title='Editar Curso', form=form, legend=f'Editar Curso: {course.title}')

@app.route('/admin/delete_course/<int:course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    if not current_user.is_admin:
        abort(403)
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Curso removido com sucesso!')
    return redirect(url_for('manage_courses'))

@app.route('/admin/course/<int:course_id>/manage', methods=['GET'])
@login_required
def manage_course(course_id):
    if not current_user.is_admin:
        abort(403)
    course = Course.query.get_or_404(course_id)
    module_form = ModuleForm()
    auth_form = AuthorizeUserForm()
    authorized_users = course.authorized_users
    modules = course.modules.order_by(Module.order).all()
    return render_template('admin/manage_course.html', title=f"Gerenciar {course.title}", 
                           course=course, module_form=module_form, auth_form=auth_form,
                           authorized_users=authorized_users, modules=modules)

@app.route('/admin/course/<int:course_id>/authorize', methods=['POST'])
@login_required
def authorize_user(course_id):
    if not current_user.is_admin:
        abort(403)
    course = Course.query.get_or_404(course_id)
    form = AuthorizeUserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash(f"Usuário com e-mail {form.email.data} não encontrado.", 'danger')
        else:
            is_authorized = CourseAuthorization.query.filter_by(user_id=user.id, course_id=course.id).first()
            if is_authorized:
                flash(f"Usuário {user.full_name} já tem acesso a este curso.", 'warning')
            else:
                authorization = CourseAuthorization(user_id=user.id, course_id=course.id)
                db.session.add(authorization)
                db.session.commit()
                flash(f"Acesso concedido para {user.full_name}!", 'success')
    return redirect(url_for('manage_course', course_id=course_id))

@app.route('/admin/authorization/<int:auth_id>/revoke', methods=['POST'])
@login_required
def revoke_authorization(auth_id):
    if not current_user.is_admin:
        abort(403)
    authorization = CourseAuthorization.query.get_or_404(auth_id)
    course_id = authorization.course_id
    user_name = authorization.user.full_name
    db.session.delete(authorization)
    db.session.commit()
    flash(f"Acesso de {user_name} foi revogado.", 'success')
    return redirect(url_for('manage_course', course_id=course_id))

@app.route('/admin/course/<int:course_id>/add_module', methods=['POST'])
@login_required
def add_module(course_id):
    if not current_user.is_admin:
        abort(403)
    course = Course.query.get_or_404(course_id)
    form = ModuleForm()
    if form.validate_on_submit():
        new_module = Module(title=form.title.data, course_id=course.id)
        db.session.add(new_module)
        db.session.commit()
        flash('Módulo adicionado com sucesso!')
    else:
        flash('Erro ao adicionar módulo. Verifique o título.', 'danger')
    return redirect(url_for('manage_course', course_id=course.id))

@app.route('/admin/edit_module/<int:module_id>', methods=['GET', 'POST'])
@login_required
def edit_module(module_id):
    if not current_user.is_admin:
        abort(403)
    module = Module.query.get_or_404(module_id)
    form = ModuleForm()
    if form.validate_on_submit():
        module.title = form.title.data
        db.session.commit()
        flash('Módulo atualizado com sucesso!')
        return redirect(url_for('manage_course', course_id=module.course_id))
    elif request.method == 'GET':
        form.title.data = module.title
    return render_template('admin/module_form.html', title='Editar Módulo', form=form, legend=f'Editar Módulo: {module.title}', module=module)

@app.route('/admin/delete_module/<int:module_id>', methods=['POST'])
@login_required
def delete_module(module_id):
    if not current_user.is_admin:
        abort(403)
    module = Module.query.get_or_404(module_id)
    course_id = module.course_id 
    db.session.delete(module)
    db.session.commit()
    flash('Módulo removido com sucesso!')
    return redirect(url_for('manage_course', course_id=course_id))

@app.route('/admin/module/<int:module_id>/manage_lessons', methods=['GET'])
@login_required
def manage_lessons(module_id):
    if not current_user.is_admin:
        abort(403)
    module = Module.query.get_or_404(module_id)
    form = LessonForm()
    return render_template('admin/manage_lessons.html', title=f"Gerenciar Lições do {module.title}", module=module, form=form)

@app.route('/admin/module/<int:module_id>/add_lesson', methods=['POST'])
@login_required
def add_lesson(module_id):
    if not current_user.is_admin:
        abort(403)
    module = Module.query.get_or_404(module_id)
    form = LessonForm()
    if form.validate_on_submit():
        new_lesson = Lesson(
            title=form.title.data, 
            content=form.content.data, 
            module_id=module.id,
            has_response_field=form.has_response_field.data
        )
        db.session.add(new_lesson)
        db.session.commit()
        flash('Lição adicionada com sucesso!')
    else:
        flash('Erro ao adicionar lição. Verifique os campos.', 'danger')
    return redirect(url_for('manage_lessons', module_id=module.id))

@app.route('/admin/edit_lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def edit_lesson(lesson_id):
    if not current_user.is_admin:
        abort(403)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = LessonForm()
    link_form = LinkForm()
    file_form = FileForm()
    if form.validate_on_submit():
        lesson.title = form.title.data
        lesson.content = form.content.data
        lesson.has_response_field = form.has_response_field.data
        db.session.commit()
        flash('Lição atualizada com sucesso!')
        return redirect(url_for('edit_lesson', lesson_id=lesson.id))
    elif request.method == 'GET':
        form.title.data = lesson.title
        form.content.data = lesson.content
        form.has_response_field.data = lesson.has_response_field
    return render_template('admin/lesson_form.html', title='Editar Lição', 
                           lesson=lesson, form=form, link_form=link_form, file_form=file_form)

@app.route('/admin/delete_lesson/<int:lesson_id>', methods=['POST'])
@login_required
def delete_lesson(lesson_id):
    if not current_user.is_admin:
        abort(403)
    lesson = Lesson.query.get_or_404(lesson_id)
    module_id = lesson.module_id 
    db.session.delete(lesson)
    db.session.commit()
    flash('Lição removida com sucesso!')
    return redirect(url_for('manage_lessons', module_id=module_id))

@app.route('/admin/lesson/<int:lesson_id>/add_link', methods=['POST'])
@login_required
def add_link(lesson_id):
    if not current_user.is_admin:
        abort(403)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = LinkForm()
    if form.validate_on_submit():
        attachment = LessonAttachment(lesson_id=lesson.id, display_name=form.display_name.data, attachment_type='link', url_or_filename=form.url.data)
        db.session.add(attachment)
        db.session.commit()
        flash('Link adicionado com sucesso!')
    else:
        flash('Erro ao adicionar link.', 'danger')
    return redirect(url_for('edit_lesson', lesson_id=lesson.id))

@app.route('/admin/lesson/<int:lesson_id>/add_file', methods=['POST'])
@login_required
def add_file(lesson_id):
    if not current_user.is_admin:
        abort(403)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = FileForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        attachment = LessonAttachment(lesson_id=lesson.id, display_name=form.display_name.data, attachment_type='file', url_or_filename=filename)
        db.session.add(attachment)
        db.session.commit()
        flash('Arquivo enviado com sucesso!')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erro no campo '{getattr(form, field).label.text}': {error}", 'danger')
    return redirect(url_for('edit_lesson', lesson_id=lesson.id))

@app.route('/admin/attachment/<int:attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(attachment_id):
    if not current_user.is_admin:
        abort(403)
    attachment = LessonAttachment.query.get_or_404(attachment_id)
    lesson_id = attachment.lesson_id
    if attachment.attachment_type == 'file':
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], attachment.url_or_filename))
        except OSError as e:
            flash(f'Erro ao remover o arquivo do disco: {e}', 'danger')
    db.session.delete(attachment)
    db.session.commit()
    flash('Anexo removido com sucesso!')
    return redirect(url_for('edit_lesson', lesson_id=lesson_id))

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin/module/<int:module_id>/manage_quiz', methods=['GET', 'POST'])
@login_required
def manage_quiz(module_id):
    if not current_user.is_admin:
        abort(403)
    module = Module.query.get_or_404(module_id)
    if not module.quiz:
        quiz = Quiz(title=f"Avaliação do {module.title}", module_id=module.id)
        db.session.add(quiz)
        db.session.commit()
        flash('Quiz inicial criado para este módulo.')
        return redirect(url_for('manage_quiz', module_id=module.id))
    form = QuestionForm()
    return render_template('admin/manage_quiz.html', title=f"Gerenciar Avaliação", module=module, quiz=module.quiz, form=form)

@app.route('/admin/quiz/<int:quiz_id>/add_question', methods=['POST'])
@login_required
def add_question(quiz_id):
    if not current_user.is_admin:
        abort(403)
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuestionForm()
    if form.validate_on_submit():
        question_text = form.text.data
        new_question = Question(text=question_text, quiz_id=quiz.id)
        db.session.add(new_question)
        db.session.flush()
        choices = [form.choice1_text.data, form.choice2_text.data, form.choice3_text.data]
        correct_choice_index = int(form.correct_choice.data) - 1
        for i, choice_text in enumerate(choices):
            is_correct = (i == correct_choice_index)
            choice = Choice(text=choice_text, is_correct=is_correct, question_id=new_question.id)
            db.session.add(choice)
        db.session.commit()
        flash('Pergunta adicionada com sucesso!')
    else:
        flash('Erro ao adicionar pergunta. Verifique todos os campos.', 'danger')
    return redirect(url_for('manage_quiz', module_id=quiz.module_id))

@app.route('/admin/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    if not current_user.is_admin:
        abort(403)
    question = Question.query.get_or_404(question_id)
    form = QuestionForm()
    if form.validate_on_submit():
        question.text = form.text.data
        question.choices[0].text = form.choice1_text.data
        question.choices[1].text = form.choice2_text.data
        question.choices[2].text = form.choice3_text.data
        for choice in question.choices:
            choice.is_correct = False
        correct_index = int(form.correct_choice.data) - 1
        question.choices[correct_index].is_correct = True
        db.session.commit()
        flash('Pergunta atualizada com sucesso!')
        return redirect(url_for('manage_quiz', module_id=question.quiz.module_id))
    elif request.method == 'GET':
        form.text.data = question.text
        form.choice1_text.data = question.choices[0].text
        form.choice2_text.data = question.choices[1].text
        form.choice3_text.data = question.choices[2].text
        correct_index = [i for i, choice in enumerate(question.choices) if choice.is_correct][0]
        form.correct_choice.data = str(correct_index + 1)
    return render_template('admin/question_form.html', title='Editar Pergunta', form=form, question=question)

@app.route('/admin/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    if not current_user.is_admin:
        abort(403)
    question = Question.query.get_or_404(question_id)
    module_id = question.quiz.module_id
    db.session.delete(question)
    db.session.commit()
    flash('Pergunta removida com sucesso!')
    return redirect(url_for('manage_quiz', module_id=module_id))


# --- ROTAS PÚBLICAS (DO ALUNO) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Email ou senha inválidos')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'Login bem-sucedido para o usuário {user.full_name}!')
        return redirect(url_for('index'))
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data, email=form.email.data, cpf=form.cpf.data,
            birth_date=form.birth_date.data, phone=form.phone.data, city=form.city.data,
            state=form.state.data, gender=form.gender.data, education_level=form.education_level.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Parabéns, você foi cadastrado com sucesso!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Cadastre-se', form=form)

@app.route('/courses')
@login_required
def courses():
    page = request.args.get('page', 1, type=int)
    courses_pagination = Course.query.order_by(Course.title).paginate(page=page, per_page=10)
    return render_template('courses.html', title='Todos os Cursos', courses=courses_pagination)

@app.route('/my_courses')
@login_required
def my_courses():
    enrollments = Enrollment.query.filter_by(student=current_user).all()
    courses = [enrollment.course for enrollment in enrollments]
    return render_template('my_courses.html', title='Meus Cursos', courses=courses)

@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    enrollment = Enrollment.query.filter_by(student=current_user, course=course).first()
    is_authorized = False
    auth = CourseAuthorization.query.filter_by(user=current_user, course=course).first()
    if auth or current_user.is_admin:
        is_authorized = True
    course_structure = []
    is_eligible_for_certificate = False
    quiz_scores = {}
    if enrollment:
        completed_lesson_ids = {comp.lesson_id for comp in current_user.completed_lessons}
        modules = course.modules.order_by(Module.order).all()
        prev_module_completed = True
        for module in modules:
            module_info = {'module': module, 'is_locked': not prev_module_completed, 'lessons': []}
            lessons = module.lessons.order_by(Lesson.order).all()
            prev_lesson_completed = True
            for lesson in lessons:
                is_lesson_locked = not (prev_lesson_completed and not module_info['is_locked'])
                module_info['lessons'].append({'lesson': lesson, 'is_locked': is_lesson_locked, 'is_complete': lesson.id in completed_lesson_ids})
                prev_lesson_completed = lesson.id in completed_lesson_ids
            course_structure.append(module_info)
            all_lessons_in_module_ids = {l.id for l in lessons}
            prev_module_completed = all_lessons_in_module_ids.issubset(completed_lesson_ids)
        total_lessons_in_course = Lesson.query.join(Module).filter(Module.course_id == course.id).count()
        lessons_completed_count = LessonCompletion.query.filter_by(student=current_user).join(Lesson).join(Module).filter(Module.course_id == course.id).count()
        lessons_completed = (total_lessons_in_course > 0 and lessons_completed_count >= total_lessons_in_course)
        quizzes_passed = True
        modules_with_quizzes = [m for m in course.modules if m.quiz]
        if not modules_with_quizzes:
            quizzes_passed = True
        else:
            for module in modules_with_quizzes:
                best_attempt = QuizAttempt.query.filter_by(student=current_user, quiz=module.quiz).order_by(QuizAttempt.score.desc()).first()
                if not best_attempt or best_attempt.score < 75:
                    quizzes_passed = False
                    break
        if lessons_completed and quizzes_passed:
            is_eligible_for_certificate = True
        for module in course.modules:
            if module.quiz:
                best_attempt = QuizAttempt.query.filter_by(student=current_user, quiz=module.quiz).order_by(QuizAttempt.score.desc()).first()
                if best_attempt:
                    quiz_scores[module.quiz.id] = best_attempt.score
    return render_template(
        'course_detail.html', 
        title=course.title, 
        course=course, 
        enrollment=enrollment,
        is_authorized=is_authorized,
        course_structure=course_structure,
        quiz_scores=quiz_scores,
        is_eligible_for_certificate=is_eligible_for_certificate
    )

@app.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    authorization = CourseAuthorization.query.filter_by(user=current_user, course=course).first()
    if not authorization and not current_user.is_admin:
        flash('Você não tem permissão para se matricular neste curso.', 'danger')
        return redirect(url_for('course_detail', course_id=course.id))
    existing_enrollment = Enrollment.query.filter_by(student=current_user, course=course).first()
    if existing_enrollment: 
        flash('Você já está matriculado neste curso.')
    else:
        new_enrollment = Enrollment(student=current_user, course=course)
        db.session.add(new_enrollment)
        db.session.commit()
        flash('Matrícula realizada com sucesso!')
    return redirect(url_for('course_detail', course_id=course.id))

@app.route('/lesson/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.module.course
    enrollment = Enrollment.query.filter_by(student=current_user, course=course).first()
    if not enrollment:
        flash('Você precisa estar matriculado no curso para ver esta lição.')
        return redirect(url_for('course_detail', course_id=course.id))
    html_content = markdown.markdown(lesson.content, extensions=['fenced_code', 'tables'])
    completion = LessonCompletion.query.filter_by(student=current_user, lesson=lesson).first()
    existing_response = LessonResponse.query.filter_by(student=current_user, lesson=lesson).first()
    response_form = LessonResponseForm()
    return render_template('lesson_detail.html', title=lesson.title, lesson=lesson, 
                           html_content=html_content, completion=completion,
                           response_form=response_form, existing_response=existing_response)

@app.route('/lesson/<int:lesson_id>/submit_response', methods=['POST'])
@login_required
def submit_response(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    form = LessonResponseForm()
    existing_response = LessonResponse.query.filter_by(student=current_user, lesson=lesson).first()
    if existing_response:
        flash('Você já enviou uma resposta para esta lição.')
        return redirect(url_for('lesson_detail', lesson_id=lesson.id))
    if form.validate_on_submit():
        response = LessonResponse(
            response_text=form.response_text.data,
            student=current_user,
            lesson=lesson
        )
        db.session.add(response)
        db.session.commit()
        flash('Sua resposta foi enviada com sucesso!')
    else:
        flash('Ocorreu um erro. Sua resposta precisa ter pelo menos 10 caracteres.', 'danger')
    return redirect(url_for('lesson_detail', lesson_id=lesson.id))

@app.route('/complete_lesson/<int:lesson_id>', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    existing_completion = LessonCompletion.query.filter_by(student=current_user, lesson=lesson).first()
    if existing_completion: flash('Lição já marcada como concluída.')
    else:
        new_completion = LessonCompletion(student=current_user, lesson=lesson)
        db.session.add(new_completion)
        db.session.commit()
        flash('Lição concluída com sucesso!')
    return redirect(url_for('course_detail', course_id=lesson.module.course.id))

@app.route('/quiz/<int:quiz_id>')
@login_required
def quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('quiz.html', title=quiz.title, quiz=quiz)

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    total_questions = quiz.questions.count()
    correct_answers = 0
    for question in quiz.questions:
        submitted_choice_id = request.form.get(f'question_{question.id}')
        if submitted_choice_id:
            correct_choice = Choice.query.filter_by(question_id=question.id, is_correct=True).first()
            if int(submitted_choice_id) == correct_choice.id:
                correct_answers += 1
    score = (correct_answers / total_questions) * 100
    attempt = QuizAttempt(student=current_user, quiz=quiz, score=score)
    db.session.add(attempt)
    db.session.commit()
    flash(f'Sua pontuação de {score:.2f}% foi salva com sucesso!')
    return redirect(url_for('course_detail', course_id=quiz.module.course_id))

@app.route('/generate_certificate/<int:course_id>')
@login_required
def generate_certificate(course_id):
    course = Course.query.get_or_404(course_id)
    logo_path = os.path.join(app.root_path, 'static', 'images', 'logo_funjab.jpg')
    logo_url = pathlib.Path(logo_path).as_uri()
    html = render_template('certificate.html', 
                           student_name=current_user.full_name, 
                           student_cpf=current_user.cpf,
                           course_title=course.title,
                           course_load=course.course_load,
                           completion_date=datetime.utcnow().strftime('%d/%m/%Y'),
                           logo_url=logo_url)
    
    pdf = HTML(string=html, base_url=request.url_root).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=certificado_{course.title}.pdf'
    return response

# ROTA DE PERFIL ATUALIZADA
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('A senha atual está incorreta.', 'danger')
            return redirect(url_for('profile'))
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Sua senha foi alterada com sucesso!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', title='Meu Perfil', form=form)

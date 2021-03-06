from flask_admin import AdminIndexView
from flask_login import current_user
from flask import redirect, url_for, request, flash
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules
from flask_ckeditor import CKEditorField
from wtforms import PasswordField
from flask_bcrypt import generate_password_hash
import re


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()
    
    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        req = re.findall(r'[0-9]+(.+)', request.url)[0]
        return redirect(url_for('login', next=req))
    

class UserAdminView(ModelView):
    column_searchable_list = ('username',)
    column_sortable_list = ('username', 'admin')
    column_exclude_list = ('password_hash',)
    form_excluded_columns = ('password_hash',)
    form_edit_rules = ('username', 'admin')
    
    form_edit_rules = (
        'username', 'admin',
        rules.Header('Reset Password'),
        'new_password', 'confirm'
    )
    form_create_rules = (
        'posts', 'username', 'email', 'image_file', 'about_me', 'last_seen', 'password', 'admin'
    )

    def scaffold_form(self):
        form_class = super(UserAdminView, self).scaffold_form()
        form_class.password = PasswordField('Password')
        form_class.new_password = PasswordField('New Password')
        form_class.confirm = PasswordField('Confirm')
        return form_class

    def create_model(self, form):
        password_hash = generate_password_hash(form.password.data)
        model = self.model(
        username=form.username.data, email=form.email.data,
        image_file=form.image_file.data, about_me=form.about_me.data,
        last_seen=form.last_seen.data, password_hash=password_hash,
        admin=form.admin.data
        )
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()
    
    def update_model(self, form, model):
        form.populate_obj(model)
        if form.new_password.data:
            if form.new_password.data != form.confirm.data:
                flash('Passwords must match', 'warning')
                return
            model.password_hash = generate_password_hash(form.new_password.data)
        self.session.add(model)
        self._on_model_change(form, model, False)
        self.session.commit()

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()
    
    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        req = re.findall(r'[0-9]+(.+)', request.url)[0]
        return redirect(url_for('login', next=req))


class PostAdminView(ModelView):
    form_overrides = dict(body=CKEditorField)
    create_template = 'edit.html'
    edit_template = 'edit.html'
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()
    
    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        req = re.findall(r'[0-9]+(.+)', request.url)[0]
        return redirect(url_for('login', next=req))

import os
import secrets

from PIL import Image
from flask import render_template, redirect, flash, url_for, request, current_app
from flask_breadcrumbs import register_breadcrumb
from flask_login import login_required

from Golden_Leaf.models import Product, db, Category
from Golden_Leaf.views.product import blueprint_product
from Golden_Leaf.views.product.forms import NewProductForm, SearchProductForm, UpdateProductForm


def view_category_dlc(*args, **kwargs):
    id = request.view_args['id']
    p = Product.query.get(id)
    return [{'text': p.description}]


@blueprint_product.route('/product', methods=['GET'])
@register_breadcrumb(blueprint_product, '.', 'Produtos')
def get_products():
    page = request.args.get('page', 1, type=int)
    products = Product.query.order_by(Product.description).paginate(page=page, per_page=10)
    return render_template('product/list.html', all_products=products)


@blueprint_product.route('/product/available/list', methods=['GET'])
@register_breadcrumb(blueprint_product, '.available_products', 'Produtos em falta')
def available_products():
    page = request.args.get('page', 1, type=int)
    products = Product.query.filter_by(is_available=False).order_by(Product.description).paginate(page=page, per_page=10)
    return render_template('product/list.html', all_products=products)


@blueprint_product.route('/product/new', methods=['GET', 'POST'])
@register_breadcrumb(blueprint_product, '.new_product', 'Novo Produto')
@login_required
def new_product():
    form = NewProductForm()
    form.category.choices = [(category.id, category.title) for category in
                             Category.query.order_by(Category.title).all()]

    if form.validate_on_submit():
        category = Category.query.filter_by(id=form.category.data).one()
        db.session.add(Product(form.category.data,
                               form.description.data,
                               form.unit_cost.data,
                               form.code.data))

        db.session.commit()
        flash(form.description.data + ' inserido com sucesso!', 'success')
        return redirect(url_for('blueprint_product.get_products'))
    return render_template('product/new.html', form=form)


@blueprint_product.route('/product/search', methods=["GET", 'POST'])
@register_breadcrumb(blueprint_product, '.search_product', 'Busca de Produto')
def search_product():
    page = request.args.get('page', 1, type=int)
    form = SearchProductForm()
    products = None
    term = None
    if form.validate_on_submit():
        if form.description.data is not "":
            term = form.description.data
            products = Product.query.filter(Product.brand.like('%' + term + '%')).paginate(page=page,
                                                                                           per_page=10)
        elif form.code.data is not "":
            term = form.code.data
            products = Product.query.filter_by(code=term).paginate(page=page, per_page=10)

        if not products:
            flash('Produto algum encontrado', 'warning')
            return redirect(url_for('blueprint_product.search_product'))
        else:
            flash('Mostrando todos os produtos com "{}" encontrados'.format(term), 'info')
            return render_template('product/list.html', all_products=products)

    return render_template('product/search.html', form=form)


@blueprint_product.route('/product/<int:id>/update', methods=["GET", 'POST'])
@register_breadcrumb(blueprint_product, '.id', '', dynamic_list_constructor=view_category_dlc)
@login_required
def update_product(id):
    product = Product.query.filter_by(id=id).one()
    form = UpdateProductForm(categories=product.category)
    if form.validate_on_submit():
        product.category = form.categories.data
        product.description = form.description.data
        product.unit_cost = form.unit_cost.data
        product.is_available = form.is_available.data
        db.session.add(product)
        db.session.commit()
        flash('Produto atualizada com sucesso.', 'success')
        return redirect(url_for('blueprint_product.update_product', id=product.id))
    elif request.method == 'GET':
        form.description.data = product.description
        form.unit_cost.data = product.unit_cost
        form.code.data = product.code
        form.is_available.data = product.is_available
    image_file = url_for('static', filename='product_pic/' + product.image_file)
    return render_template('product/edit.html', form=form, image_file=image_file)



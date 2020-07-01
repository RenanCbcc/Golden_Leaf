class CategoryService {
    importCategories(handler) {
        return fetch('http://127.0.0.1:5000/api/category')
            .then(res => handler(res))
            .then(res => res.json())
            .then((data) => data.map(c => new Category(c.id, c.title))).catch(err => { throw new Error(err); });
    }
}
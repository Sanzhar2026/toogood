// 1. Проверьте, есть ли cookies
console.log('Cookies:', document.cookie);

// 2. Проверьте статус курьера
fetch('https://toogood-2ncf.onrender.com/api/courier/status', {
  credentials: 'include'
})
.then(r => {
  console.log('Статус ответа:', r.status);
  return r.json();
})
.then(data => console.log('Ответ:', data))
.catch(err => console.error('Ошибка:', err));
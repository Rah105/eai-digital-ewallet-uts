const bcrypt = require('bcryptjs');

// Kata sandi yang ingin di-hash
const password = 'admin123';
// Salt rounds (harus sama dengan yang digunakan pada hash lama, yaitu 10)
const saltRounds = 10; 

bcrypt.hash(password, saltRounds, (err, hash) => {
    if (err) {
        console.error(err);
    } else {
        console.log(`Password: ${password}`);
        console.log(`New Hash: ${hash}`);
    }
});
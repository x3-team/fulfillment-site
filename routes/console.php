<?php

use App\Models\User;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Str;

// php artisan admin:create почта@домен "Имя" — создаёт админа или меняет ему пароль
Artisan::command('admin:create {email} {name=Админ} {--password=}', function (string $email, string $name) {
    $password = $this->option('password') ?: Str::password(14, symbols: false);
    User::updateOrCreate(['email' => $email], ['name' => $name, 'password' => $password, 'is_admin' => true]);
    $this->info("Готово. Вход: /admin, почта {$email}, пароль {$password}");
})->purpose('Создать администратора сайта');

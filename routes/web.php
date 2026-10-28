<?php

use App\Http\Controllers\Admin\AuthController;
use App\Http\Controllers\Admin\SiteController;
use App\Http\Controllers\PageController;
use Illuminate\Support\Facades\Route;

Route::prefix('admin')->middleware('inertia')->group(function () {
    Route::middleware('guest')->group(function () {
        Route::get('login', [AuthController::class, 'show'])->name('login');
        Route::post('login', [AuthController::class, 'login'])->middleware('throttle:10,1');
    });
    Route::post('logout', [AuthController::class, 'logout'])->middleware('auth');

    Route::middleware(['auth', 'admin'])->group(function () {
        Route::redirect('/', '/admin/calculator');
        Route::get('calculator', [SiteController::class, 'calculator']);
        Route::put('calculator', [SiteController::class, 'saveCalculator']);
        Route::get('contacts', [SiteController::class, 'contacts']);
        Route::put('contacts', [SiteController::class, 'saveContacts']);
        Route::get('texts', [SiteController::class, 'texts']);
        Route::put('texts', [SiteController::class, 'saveTexts']);
        Route::get('seo', [SiteController::class, 'seo']);
        Route::put('seo', [SiteController::class, 'saveSeo']);
        Route::post('reset/{section}', [SiteController::class, 'reset']);
    });
});

// Все остальные адреса — страницы сайта из public/ с настройками из админки
Route::get('/{path?}', PageController::class)->where('path', '^(?!admin(/|$)).*');

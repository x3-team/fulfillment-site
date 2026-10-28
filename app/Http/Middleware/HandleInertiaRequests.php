<?php

namespace App\Http\Middleware;

use Illuminate\Http\Request;
use Inertia\Middleware;

class HandleInertiaRequests extends Middleware
{
    protected $rootView = 'admin';

    public function share(Request $request): array
    {
        return [
            ...parent::share($request),
            'user' => fn () => $request->user()?->only('name', 'email'),
            'flash' => fn () => $request->session()->get('ok'),
        ];
    }
}

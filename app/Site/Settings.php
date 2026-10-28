<?php

namespace App\Site;

use App\Models\Setting;
use Illuminate\Support\Facades\Cache;

/** Настройки сайта из админки. Каждое сохранение меняет версию, и кэш страниц сбрасывается. */
class Settings
{
    public function get(string $key, mixed $default = null): mixed
    {
        return $this->all()[$key] ?? $default;
    }

    public function all(): array
    {
        return Cache::rememberForever('site.settings.'.$this->version(), fn () => Setting::all()->pluck('value', 'key')->all());
    }

    public function put(string $key, mixed $value): void
    {
        Setting::updateOrCreate(['key' => $key], ['value' => $value]);
        Cache::forever('site.version', $this->version() + 1);
    }

    public function forget(string $key): void
    {
        Setting::whereKey($key)->delete();
        Cache::forever('site.version', $this->version() + 1);
    }

    public function version(): int
    {
        return (int) Cache::get('site.version', 1);
    }
}

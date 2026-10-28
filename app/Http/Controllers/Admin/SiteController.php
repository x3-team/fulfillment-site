<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Site\PageRenderer;
use App\Site\Settings;
use Illuminate\Http\Request;
use Inertia\Inertia;

/** Разделы админки. Каждый раздел — одна запись в settings; «Вернуть как было» удаляет её. */
class SiteController extends Controller
{
    public function __construct(private Settings $settings, private PageRenderer $pages) {}

    public function calculator()
    {
        return $this->page('Calculator', 'calculator');
    }

    public function saveCalculator(Request $request)
    {
        $item = fn ($g) => [
            "$g" => 'array',
            "$g.*.id" => ['required', 'regex:/^[a-z0-9_]+$/', 'distinct'],
            "$g.*.name" => 'required|string|max:120',
            "$g.*.sub" => 'nullable|string|max:300',
            "$g.*.label" => 'nullable|string|max:120',
            "$g.*.price" => 'required|numeric|min:0',
            "$g.*.per" => 'nullable|string|max:40',
            "$g.*.on" => 'boolean',
        ];
        $data = $request->validate([
            'accept' => 'required|numeric|min:0',
            'discount' => 'required|numeric|min:0|max:100',
            'storage.rate' => 'required|numeric|min:0',
            'storage.free_days' => 'required|integer|min:0',
            ...$item('unload'), 'unload' => 'required|array|min:1', 'unload.*.qty' => 'required|integer|min:1',
            ...$item('work'), ...$item('fbs'), ...$item('fbo'),
        ]);
        $clean = fn ($items) => array_map(fn ($it) => [
            'id' => $it['id'], 'name' => $it['name'], 'sub' => $it['sub'] ?? '', 'label' => $it['label'] ?? '',
            'price' => 0 + $it['price'], 'per' => $it['per'] ?? '', 'on' => (bool) ($it['on'] ?? false),
        ] + (isset($it['qty']) ? ['qty' => (int) $it['qty']] : []), array_values($items ?? []));
        $calc = [
            'accept' => 0 + $data['accept'],
            'discount' => 0 + $data['discount'],
            'storage' => ['rate' => 0 + $data['storage']['rate'], 'free_days' => (int) $data['storage']['free_days']],
        ];
        foreach (['unload', 'work', 'fbs', 'fbo'] as $g) {
            $calc[$g] = $clean($data[$g] ?? []);
        }

        return $this->save('calculator', $calc);
    }

    public function contacts()
    {
        return $this->page('Contacts', 'contacts', ['fields' => config('site.contacts')]);
    }

    public function saveContacts(Request $request)
    {
        $data = $request->validate([
            'phone' => ['required', 'string', 'max:40', 'regex:/^[\d\s()+-]+$/'],
            'telegram' => ['required', 'url:https', 'starts_with:https://t.me/'],
            'address' => 'required|string|max:200',
        ]);

        return $this->save('contacts', $data);
    }

    public function texts()
    {
        return $this->page('Texts', 'texts', [
            'labels' => config('site.texts'),
            'faq' => $this->settings->get('faq') ?? $this->pages->defaults()['faq'],
            'faqDefault' => $this->pages->defaults()['faq'],
            'faqChanged' => $this->settings->get('faq') !== null,
        ]);
    }

    public function saveTexts(Request $request)
    {
        $keys = array_keys(config('site.texts'));
        $data = $request->validate([
            'texts' => 'array',
            'texts.*' => 'nullable|string|max:2000',
            'faq' => 'array',
            'faq.*.q' => 'required|string|max:300',
            'faq.*.a' => 'required|string|max:3000',
        ]);
        $defaults = $this->pages->defaults();
        $texts = array_filter(array_intersect_key($data['texts'] ?? [], array_flip($keys)), fn ($v, $k) => $v !== null && $v !== ($defaults['texts'][$k] ?? null), ARRAY_FILTER_USE_BOTH);
        $texts ? $this->settings->put('texts', $texts) : $this->settings->forget('texts');
        $faq = array_map(fn ($f) => ['q' => $f['q'], 'a' => $f['a']], array_values($data['faq'] ?? []));
        $faq && $faq !== $defaults['faq'] ? $this->settings->put('faq', $faq) : $this->settings->forget('faq');

        return back()->with('ok', 'Сохранено, на сайте уже новые тексты');
    }

    public function seo()
    {
        return $this->page('Seo', 'seo', ['pages' => config('site.pages')]);
    }

    public function saveSeo(Request $request)
    {
        $paths = array_keys(config('site.pages'));
        $data = $request->validate([
            'pages' => 'array',
            'pages.*.title' => 'nullable|string|max:120',
            'pages.*.description' => 'nullable|string|max:300',
        ]);
        $defaults = $this->pages->defaults()['seo'];
        $seo = [];
        foreach ($data['pages'] ?? [] as $path => $p) {
            if (! in_array($path, $paths, true)) {
                continue;
            }
            $p = array_filter(['title' => trim($p['title'] ?? ''), 'description' => trim($p['description'] ?? '')], fn ($v, $k) => $v !== '' && $v !== ($defaults[$path][$k] ?? null), ARRAY_FILTER_USE_BOTH);
            if ($p) {
                $seo[$path] = $p;
            }
        }

        return $this->save('seo', $seo ?: null);
    }

    public function reset(string $section)
    {
        abort_unless(in_array($section, ['calculator', 'contacts', 'texts', 'seo'], true), 404);
        $this->settings->forget($section);
        if ($section === 'texts') {
            $this->settings->forget('faq');
        }

        return back()->with('ok', 'Вернули как в вёрстке');
    }

    private function page(string $component, string $key, array $extra = [])
    {
        $default = $this->pages->defaults()[$key];
        $value = $this->settings->get($key);
        if (in_array($key, ['texts', 'seo'], true)) {
            $value = array_replace_recursive($default, $value ?? []);
        }

        return Inertia::render($component, [
            'value' => $value ?? $default,
            'default' => $default,
            'changed' => $this->settings->get($key) !== null,
            ...$extra,
        ]);
    }

    private function save(string $key, mixed $value)
    {
        $value === null ? $this->settings->forget($key) : $this->settings->put($key, $value);

        return back()->with('ok', 'Сохранено, на сайте уже новая версия');
    }
}

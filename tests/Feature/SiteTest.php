<?php

namespace Tests\Feature;

use App\Models\User;
use App\Site\PageRenderer;
use App\Site\Settings;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class SiteTest extends TestCase
{
    use RefreshDatabase;

    private function admin(): User
    {
        return User::factory()->create(['is_admin' => true]);
    }

    public function test_pages_without_settings_are_served_as_is(): void
    {
        $this->get('/')->assertOk()->assertSee('const CALC_DEFAULT=', false);
        $this->assertSame(file_get_contents(public_path('index.html')), $this->get('/')->getContent());
        $this->get('/kontakty/')->assertOk()->assertSee('+7 (916) 728-42-46');
        $this->get('/kontakty')->assertRedirect('/kontakty/');
        $this->get('/net-takoy-stranicy/')->assertNotFound();
        $this->get('/../.env')->assertNotFound();
    }

    public function test_defaults_are_read_from_the_template(): void
    {
        $d = app(PageRenderer::class)->defaults();
        $this->assertSame(5, $d['calculator']['accept']);
        $this->assertSame(35, $d['calculator']['unload'][0]['price']);
        $this->assertCount(6, $d['faq']);
        $this->assertArrayHasKey('calc_title', $d['texts']);
        $this->assertNotSame('', $d['seo']['']['title']);
    }

    public function test_admin_requires_login(): void
    {
        $this->get('/admin/calculator')->assertRedirect('/admin/login');
        $this->actingAs(User::factory()->create())->get('/admin/calculator')->assertForbidden();
        $this->actingAs($this->admin())->get('/admin/calculator')->assertOk();
    }

    public function test_login(): void
    {
        $this->artisan('admin:create', ['email' => 'a@tovarvdele.ru', '--password' => 'secret-pass'])->assertOk();
        $this->post('/admin/login', ['email' => 'a@tovarvdele.ru', 'password' => 'wrong'])->assertSessionHasErrors('email');
        $this->post('/admin/login', ['email' => 'a@tovarvdele.ru', 'password' => 'secret-pass'])->assertRedirect('/admin');
    }

    public function test_calculator_prices_reach_the_page(): void
    {
        $calc = app(PageRenderer::class)->defaults()['calculator'];
        $calc['accept'] = 7;
        $calc['discount'] = 15;
        $calc['storage']['free_days'] = 10;
        $calc['work'][0]['name'] = 'Маркировка </script> тест';
        $this->actingAs($this->admin())->put('/admin/calculator', $calc)->assertSessionHasNoErrors();

        $html = $this->get('/')->getContent();
        $this->assertStringContainsString('"accept":7', $html);
        $this->assertStringContainsString('Маркировка \\u003C/script\\u003E тест', $html);
        $this->assertStringNotContainsString('Маркировка </script>', $html);
        $this->assertStringContainsString('<span class="cfg-disc">15</span>', $html);
        $this->assertStringContainsString('<span class="cfg-free">10</span>', $html);

        $this->post('/admin/reset/calculator');
        $this->assertSame(file_get_contents(public_path('index.html')), $this->get('/')->getContent());
    }

    public function test_calculator_validation(): void
    {
        $calc = app(PageRenderer::class)->defaults()['calculator'];
        $calc['work'][0]['price'] = -1;
        $this->actingAs($this->admin())->put('/admin/calculator', $calc)->assertSessionHasErrors('work.0.price');
    }

    public function test_contacts_change_on_all_fulfillment_pages(): void
    {
        $this->actingAs($this->admin())->put('/admin/contacts', [
            'phone' => '8 (900) 111-22-33', 'telegram' => 'https://t.me/tovarvdele', 'address' => 'ул. Новая, д. 1',
        ])->assertSessionHasNoErrors();

        foreach (['/', '/kontakty/', '/dokumenty/politika/'] as $url) {
            $html = $this->get($url)->getContent();
            $this->assertStringNotContainsString('728-42-46', $html, $url);
            $this->assertStringContainsString('8 (900) 111-22-33', $html, $url);
            $this->assertStringContainsString('tel:+79001112233', $html, $url);
        }
        $this->assertStringContainsString('href="https://t.me/tovarvdele"', $this->get('/')->getContent());
        $this->assertStringContainsString('ул. Новая, д. 1', $this->get('/kontakty/')->getContent());
    }

    public function test_texts_and_faq(): void
    {
        $faq = [['q' => 'Новый вопрос?', 'a' => 'Новый ответ.']];
        $this->actingAs($this->admin())->put('/admin/texts', ['texts' => ['calc_title' => 'Цена за минуту'], 'faq' => $faq])->assertSessionHasNoErrors();

        $html = $this->get('/')->getContent();
        $this->assertStringContainsString('<!--t:calc_title-->Цена за минуту<!--/t-->', $html);
        $this->assertStringContainsString('const FAQ=[["Новый вопрос?","Новый ответ."]];', $html);
        $this->assertStringContainsString('<div id="faqList"><details open><summary><span class="num mono">01</span><span>Новый вопрос?</span>', $html);
        $this->assertStringContainsString('"name":"Новый вопрос?"', $html);
        $this->assertStringNotContainsString('Есть ли минимальный объём', $html);
    }

    public function test_seo(): void
    {
        $this->actingAs($this->admin())->put('/admin/seo', ['pages' => ['kontakty' => ['title' => 'Контакты склада в Туле', 'description' => 'Телефон & адрес']]])->assertSessionHasNoErrors();
        $html = $this->get('/kontakty/')->getContent();
        $this->assertStringContainsString('<title>Контакты склада в Туле</title>', $html);
        $this->assertStringContainsString('<meta name="description" content="Телефон &amp; адрес">', $html);
        $this->assertStringContainsString('<meta property="og:title" content="Контакты склада в Туле">', $html);
        $this->assertSame(['kontakty'], array_keys(app(Settings::class)->get('seo')));
    }
}

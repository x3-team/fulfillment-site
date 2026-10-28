<?php

namespace Tests;

use Illuminate\Foundation\Testing\TestCase as BaseTestCase;

abstract class TestCase extends BaseTestCase
{
    // Laravel в тестах срезает слэш в конце адреса, а сайту он важен (/kontakty/ против /kontakty)
    protected function prepareUrlForRequest($uri)
    {
        return rtrim(config('app.url'), '/').'/'.ltrim((string) $uri, '/');
    }
}

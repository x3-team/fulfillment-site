<?php

namespace App\Http\Controllers;

use App\Site\PageRenderer;
use Illuminate\Http\Request;

class PageController extends Controller
{
    public function __invoke(Request $request, PageRenderer $pages, string $path = '')
    {
        $html = $pages->render($path);
        if ($html === null) {
            abort(404);
        }
        // /kontakty → /kontakty/: страницы ссылаются на соседние файлы относительными путями
        if ($path !== '' && ! str_ends_with($request->getPathInfo(), '/')) {
            return redirect('/'.trim($path, '/').'/', 301);
        }

        return response($html)->header('Content-Type', 'text/html; charset=utf-8');
    }
}

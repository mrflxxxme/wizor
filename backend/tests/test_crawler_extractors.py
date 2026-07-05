"""Unit: извлечение сигналов и аудит-факторов (AC-2)."""

from __future__ import annotations

from wizor.crawler import extractors

_HTML_RICH = """
<html><body>
  <header><nav>меню</nav></header>
  <main>
    <article>
      <h1>Заголовок страницы</h1>
      <h2>Подзаголовок</h2>
      <h3>Секция</h3>
      <section>Контент</section>
      <script type="application/ld+json">
        {"@context":"https://schema.org","@type":"Organization","name":"Acme"}
      </script>
      <div class="faq">Часто задаваемые вопросы</div>
    </article>
  </main>
  <footer>подвал</footer>
  <a href="/about">О нас</a>
  <a href="https://external.com/x">внешняя</a>
</body></html>
"""

_HTML_BARE = "<html><body><div>только текст, без структуры</div></body></html>"


def test_extract_page_signals_rich() -> None:
    signals = extractors.extract_page_signals(_HTML_RICH)
    assert signals["h1"] == ["Заголовок страницы"]
    assert signals["h2"] == ["Подзаголовок"]
    assert "article" in signals["semantic_tags"]
    assert "nav" in signals["semantic_tags"]
    assert len(signals["json_ld_blocks"]) == 1
    assert signals["faq_detected"] is True


def test_extract_page_signals_bare() -> None:
    signals = extractors.extract_page_signals(_HTML_BARE)
    assert signals["h1"] == []
    assert signals["semantic_tags"] == []
    assert signals["json_ld_blocks"] == []
    assert signals["faq_detected"] is False


def test_discover_links_same_origin_only() -> None:
    links = extractors.discover_links(_HTML_RICH, "https://acme.ru/page")
    assert "https://acme.ru/about" in links
    assert all("external.com" not in link for link in links)


def test_robots_verdict_missing() -> None:
    verdict = extractors.robots_verdict(None)
    assert verdict.factor == "robots_txt"
    assert verdict.verdict == "warn"


def test_robots_verdict_disallow_all() -> None:
    verdict = extractors.robots_verdict("User-agent: *\nDisallow: /")
    assert verdict.verdict == "fail"
    assert verdict.data["disallow_all"] is True


def test_robots_verdict_ai_bots() -> None:
    verdict = extractors.robots_verdict("User-agent: GPTBot\nAllow: /")
    assert verdict.verdict == "pass"
    assert "GPTBot" in verdict.data["ai_bots_mentioned"]


def test_sitemap_verdict() -> None:
    assert extractors.sitemap_verdict(sitemap_present=False).verdict == "warn"
    assert extractors.sitemap_verdict(sitemap_present=True, url_count=10).verdict == "pass"


def test_http_status_verdict() -> None:
    assert extractors.http_status_verdict([200, 301, 200]).verdict == "pass"
    assert extractors.http_status_verdict([200, 404]).verdict == "warn"
    assert extractors.http_status_verdict([200, 500]).verdict == "fail"
    assert extractors.http_status_verdict([]).verdict == "fail"


def test_html_semantics_verdict() -> None:
    rich = extractors.extract_page_signals(_HTML_RICH)
    bare = extractors.extract_page_signals(_HTML_BARE)
    assert extractors.html_semantics_verdict([rich]).verdict == "pass"
    assert extractors.html_semantics_verdict([bare]).verdict == "fail"
    assert extractors.html_semantics_verdict([rich, bare]).verdict == "warn"


def test_json_ld_verdict() -> None:
    rich = extractors.extract_page_signals(_HTML_RICH)
    bare = extractors.extract_page_signals(_HTML_BARE)
    passing = extractors.json_ld_verdict([rich])
    assert passing.verdict == "pass"
    assert "Organization" in passing.data["types_found"]
    assert extractors.json_ld_verdict([bare]).verdict == "fail"


def test_faq_verdict() -> None:
    rich = extractors.extract_page_signals(_HTML_RICH)
    bare = extractors.extract_page_signals(_HTML_BARE)
    assert extractors.faq_verdict([rich]).verdict == "pass"
    assert extractors.faq_verdict([bare]).verdict == "warn"

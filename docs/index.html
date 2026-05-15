<!DOCTYPE html>
<html lang="hu">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <title>Balkán Politikai Hangulat Monitor</title>

  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <style>
    body {
      margin: 0;
      background: #f3f4f6;
      font-family: Arial, Helvetica, sans-serif;
      color: #111827;
    }

    header {
      background: #111827;
      color: white;
      padding: 30px 20px;
      text-align: center;
    }

    header h1 {
      margin: 0;
      font-size: 30px;
    }

    header p {
      margin-top: 10px;
      color: #d1d5db;
    }

    main {
      max-width: 1300px;
      margin: 24px auto;
      padding: 0 16px;
    }

    .status-box {
      background: white;
      border-radius: 14px;
      padding: 20px;
      margin-bottom: 22px;
      box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    }

    .status-box h2 {
      margin-top: 0;
      font-size: 22px;
    }

    .small {
      color: #6b7280;
      font-size: 14px;
    }

    .dashboard-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(390px, 1fr));
      gap: 22px;
    }

    .country-card {
      background: white;
      border-radius: 14px;
      border-left: 7px solid #6b7280;
      box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
      overflow: hidden;
    }

    .positive {
      border-left-color: #16a34a;
    }

    .neutral {
      border-left-color: #f59e0b;
    }

    .negative {
      border-left-color: #dc2626;
    }

    .card-inner {
      padding: 18px;
    }

    .country-title {
      font-size: 22px;
      font-weight: 700;
      margin-bottom: 14px;
    }

    .score-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 14px;
    }

    .score-box {
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 12px;
    }

    .score-label {
      color: #6b7280;
      font-size: 13px;
      margin-bottom: 5px;
    }

    .score-value {
      font-size: 32px;
      font-weight: 700;
    }

    .signal-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin-bottom: 10px;
    }

    .signal-pill {
      background: #f3f4f6;
      border-radius: 999px;
      padding: 7px 9px;
      font-size: 12px;
      color: #374151;
    }

    .topic-line,
    .source-line {
      font-size: 13px;
      color: #4b5563;
      margin-top: 8px;
      line-height: 1.4;
    }

    .social-box,
    .chart-box,
    .news-section {
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 14px;
      margin-top: 14px;
    }

    .social-box {
      background: #f9fafb;
    }

    .social-box h3,
    .chart-box h3,
    .news-section h3 {
      margin: 0 0 10px 0;
      font-size: 15px;
    }

    .chart-desc {
      font-size: 12px;
      color: #6b7280;
      margin-bottom: 12px;
      line-height: 1.4;
    }

    .chart-wrap {
      height: 250px;
    }

    .news-list {
      margin: 0;
      padding-left: 18px;
    }

    .news-list li {
      margin-bottom: 9px;
      font-size: 13px;
      line-height: 1.4;
    }

    .news-list a {
      color: #2563eb;
      text-decoration: none;
    }

    .news-list a:hover {
      text-decoration: underline;
    }

    footer {
      text-align: center;
      color: #6b7280;
      font-size: 13px;
      padding: 30px 10px;
    }
  </style>
</head>

<body>

<header>
  <h1>Balkán Politikai Hangulat Monitor</h1>
  <p>Hírindex, social signal és negatív említések kombinált áttekintése</p>
</header>

<main>

  <section class="status-box">
    <h2>Aktuális helyzetkép</h2>
    <p>
      A fő hírindex híralapú forrásokból készül. A social signal külön jelző,
      amely Reddit RSS és Mastodon hashtag RSS alapján mutat aktivitást.
    </p>

    <p class="small" id="updatedAt">Frissítés: betöltés...</p>
    <p class="small" id="sourceInfo">Hírforrás: betöltés...</p>
    <p class="small" id="socialInfo">Social forrás: betöltés...</p>
    <p class="small" id="methodNote"></p>
  </section>

  <section class="dashboard-grid" id="countryGrid"></section>

</main>

<footer>
  Balkán Politikai Hangulat Monitor – GitHub Pages
</footer>

<script>
let chartStore = {};

async function loadData() {
  try {
    const latestResponse = await fetch('./data/latest.json');
    const historyResponse = await fetch('./data/history.json');
    const socialResponse = await fetch('./data/social_latest.json');

    const latestData = await latestResponse.json();
    const historyData = await historyResponse.json();
    const socialData = await socialResponse.json();

    document.getElementById('updatedAt').textContent =
      `Frissítés: ${latestData.updated_at}`;

    document.getElementById('sourceInfo').textContent =
      `Hírforrás: ${latestData.source || 'nincs megadva'}`;

    document.getElementById('socialInfo').textContent =
      `Social forrás: ${socialData.source || 'nincs megadva'} – ${socialData.updated_at || 'nincs időpont'}`;

    document.getElementById('methodNote').textContent =
      latestData.method_note || '';

    const grid = document.getElementById('countryGrid');
    grid.innerHTML = '';

    latestData.countries.forEach(country => {
      const socialSignal = getSocialSignal(country.name, socialData);
      const chartId = `chart-${slugify(country.name)}`;

      const card = document.createElement('div');
      card.className = `country-card ${country.status}`;

      card.innerHTML = `
        <div class="card-inner">

          <div class="country-title">${country.name}</div>

          <div class="score-row">
            <div class="score-box">
              <div class="score-label">Hírindex</div>
              <div class="score-value">${country.score}</div>
              <div class="small">${getStatusText(country.status)}</div>
            </div>

            <div class="score-box">
              <div class="score-label">Social signal</div>
              <div class="score-value">${socialSignal.score || 0}</div>
              <div class="small">${getSocialLevelText(socialSignal.level)}</div>
            </div>
          </div>

          <div class="signal-grid">
            <div class="signal-pill">Cikkek: <strong>${country.article_count || 0}</strong></div>
            <div class="signal-pill">Hír negatív: <strong>${country.negative_hits || 0}</strong></div>
            <div class="signal-pill">Hír pozitív: <strong>${country.positive_hits || 0}</strong></div>
          </div>

          <div class="topic-line">
            Fő hír téma: <strong>${country.main_topic || 'nincs adat'}</strong>
          </div>

          <div class="social-box">
            <h3>Social signal</h3>

            <div class="signal-grid">
              <div class="signal-pill">Említések: <strong>${socialSignal.mentions || 0}</strong></div>
              <div class="signal-pill">Negatív: <strong>${socialSignal.negative_hits || 0}</strong></div>
              <div class="signal-pill">Pozitív: <strong>${socialSignal.positive_hits || 0}</strong></div>
            </div>

            <div class="source-line">
              Reddit: ${getSourceCount(socialSignal, 'reddit')} |
              Mastodon: ${getSourceCount(socialSignal, 'mastodon')}
            </div>

            <div class="topic-line">
              Fő social téma: <strong>${socialSignal.main_topic || 'nincs adat'}</strong>
            </div>
          </div>

          <div class="chart-box">
            <h3>Kombinált trenddiagram</h3>
            <div class="chart-desc">
              A vonal a hírindexet, az oszlopok a social aktivitást,
              a piros vonal a social negatív jeleket mutatja.
            </div>
            <div class="chart-wrap">
              <canvas id="${chartId}"></canvas>
            </div>
          </div>

          ${buildArticlesHtml(country.top_articles || [])}

        </div>
      `;

      grid.appendChild(card);

      createComboChart(chartId, country.name, historyData, socialSignal);
    });

  } catch (error) {
    console.error(error);

    document.getElementById('countryGrid').innerHTML = `
      <div class="country-card negative">
        <div class="card-inner">
          <div class="country-title">Adatbetöltési hiba</div>
          <p>Nem sikerült betölteni a latest.json, history.json vagy social_latest.json fájlt.</p>
        </div>
      </div>
    `;
  }
}

function createComboChart(canvasId, countryName, historyData, socialSignal) {
  const canvas = document.getElementById(canvasId);

  if (!canvas) {
    return;
  }

  if (chartStore[canvasId]) {
    chartStore[canvasId].destroy();
  }

  const historyRows = getCountryHistory(countryName, historyData);
  const labels = historyRows.map(row => row.date);

  if (labels.length === 0) {
    labels.push('Ma');
  }

  const newsIndex = historyRows.map(row => row.score);
  const socialMentions = historyRows.map(row => row.social_mentions || 0);
  const socialNegative = historyRows.map(row => row.social_negative_hits || 0);

  if (newsIndex.length === 0) {
    newsIndex.push(0);
  }

  if (socialMentions.length === 0) {
    socialMentions.push(socialSignal.mentions || 0);
  } else {
    socialMentions[socialMentions.length - 1] = socialSignal.mentions || 0;
  }

  if (socialNegative.length === 0) {
    socialNegative.push(socialSignal.negative_hits || 0);
  } else {
    socialNegative[socialNegative.length - 1] = socialSignal.negative_hits || 0;
  }

  chartStore[canvasId] = new Chart(canvas, {
    data: {
      labels: labels,
      datasets: [
        {
          type: 'bar',
          label: 'Social említések',
          data: socialMentions,
          yAxisID: 'ySocial',
          borderWidth: 1,
          borderRadius: 6
        },
        {
          type: 'line',
          label: 'Hírindex',
          data: newsIndex,
          yAxisID: 'yNews',
          tension: 0.35,
          borderWidth: 3,
          pointRadius: 3
        },
        {
          type: 'line',
          label: 'Social negatív jelek',
          data: socialNegative,
          yAxisID: 'ySocial',
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            boxWidth: 12,
            font: {
              size: 11
            }
          }
        },
        tooltip: {
          backgroundColor: '#111827',
          padding: 10
        }
      },
      scales: {
        yNews: {
          type: 'linear',
          position: 'left',
          min: -30,
          max: 30,
          title: {
            display: true,
            text: 'Hírindex'
          },
          grid: {
            color: 'rgba(0,0,0,0.06)'
          }
        },
        ySocial: {
          type: 'linear',
          position: 'right',
          beginAtZero: true,
          title: {
            display: true,
            text: 'Social signal'
          },
          grid: {
            drawOnChartArea: false
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      }
    }
  });
}

function getCountryHistory(countryName, historyData) {
  const rows = [];
  const records = historyData.records || [];

  records.forEach(record => {
    const country = record.countries.find(item => item.name === countryName);

    if (country) {
      rows.push({
        date: record.date,
        score: country.score || 0,
        social_mentions: country.social_mentions || 0,
        social_negative_hits: country.social_negative_hits || 0
      });
    }
  });

  return rows.slice(-7);
}

function getSocialSignal(countryName, socialData) {
  const fallback = {
    score: 0,
    level: 'low',
    mentions: 0,
    negative_hits: 0,
    positive_hits: 0,
    source_counts: {},
    main_topic: 'nincs adat'
  };

  if (!socialData || !socialData.countries) {
    return fallback;
  }

  const row = socialData.countries.find(item => item.name === countryName);

  if (!row || !row.social_signal) {
    return fallback;
  }

  return row.social_signal;
}

function getSourceCount(socialSignal, sourceName) {
  if (!socialSignal || !socialSignal.source_counts) {
    return 0;
  }

  return socialSignal.source_counts[sourceName] || 0;
}

function buildArticlesHtml(articles) {
  if (!articles.length) {
    return `
      <div class="news-section">
        <h3>Kiemelt cikkek</h3>
        <p class="small">Nincs megjeleníthető cikk.</p>
      </div>
    `;
  }

  const items = articles.slice(0, 5).map(article => {
    const title = article.title || 'Cím nélkül';
    const url = article.url || '#';
    const source = article.source || 'ismeretlen forrás';

    return `
      <li>
        <a href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>
        <br>
        <span class="small">${source}</span>
      </li>
    `;
  }).join('');

  return `
    <div class="news-section">
      <h3>Kiemelt cikkek</h3>
      <ul class="news-list">${items}</ul>
    </div>
  `;
}

function getStatusText(status) {
  if (status === 'positive') {
    return 'pozitív';
  }

  if (status === 'negative') {
    return 'negatív';
  }

  return 'semleges';
}

function getSocialLevelText(level) {
  if (level === 'high') {
    return 'magas aktivitás';
  }

  if (level === 'medium') {
    return 'közepes aktivitás';
  }

  return 'alacsony aktivitás';
}

function slugify(text) {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

loadData();
</script>

</body>
</html>

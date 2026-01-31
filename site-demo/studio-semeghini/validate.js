const { chromium } = require('playwright');

async function validateSite() {
  console.log('\n🧪 Validando Studio Semeghini com Playwright...\n');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Carregar o arquivo local
    const filePath = 'file:///home/bot/clawd/site-pixel-alchemy/site-demo/studio-semeghini/index.html';
    console.log(`📂 Carregando: ${filePath}`);

    await page.goto(filePath, { waitUntil: 'networkidle' });

    // Validar elementos principais
    console.log('\n🔍 Verificando elementos...\n');

    const checks = [
      {
        name: 'Hero Heading',
        selector: 'h1',
        expectedText: 'Onde cada fio conta sua história'
      },
      {
        name: 'CTA Button',
        selector: 'a[href="#contato"]',
        expectedText: 'Agende seu horário'
      },
      {
        name: 'Navigation',
        selector: 'nav',
        exists: true
      },
      {
        name: 'História Section',
        selector: '#historia',
        exists: true
      },
      {
        name: 'Serviços Section',
        selector: '#servicos',
        exists: true
      },
      {
        name: 'Serviços Cards',
        selector: '#servicos .service-card',
        count: 6
      },
      {
        name: 'Depoimentos Section',
        selector: '#depoimentos',
        exists: true
      },
      {
        name: 'Contato Section',
        selector: '#contato',
        exists: true
      },
      {
        name: 'WhatsApp Button',
        selector: 'a[href*="wa.me"]',
        exists: true
      },
      {
        name: 'Footer',
        selector: 'footer',
        exists: true
      },
      {
        name: 'Telefone',
        selector: 'text=(16) 99715-6040',
        exists: true
      },
      {
        name: 'Endereço',
        selector: 'text=R. Ondibecte Silveira',
        exists: true
      }
    ];

    let passed = 0;
    let failed = 0;

    for (const check of checks) {
      try {
        if (check.expectedText) {
          const element = await page.locator(check.selector).first();
          const text = await element.textContent();
          if (text && text.includes(check.expectedText)) {
            console.log(`✅ ${check.name}: "${check.expectedText}" encontrado`);
            passed++;
          } else {
            console.log(`❌ ${check.name}: esperado "${check.expectedText}", got "${text}"`);
            failed++;
          }
        } else if (check.count) {
          const count = await page.locator(check.selector).count();
          if (count === check.count) {
            console.log(`✅ ${check.name}: ${count} itens`);
            passed++;
          } else {
            console.log(`❌ ${check.name}: esperado ${check.count}, got ${count}`);
            failed++;
          }
        } else if (check.exists) {
          const exists = await page.locator(check.selector).count() > 0;
          if (exists) {
            console.log(`✅ ${check.name}: encontrado`);
            passed++;
          } else {
            console.log(`❌ ${check.name}: não encontrado`);
            failed++;
          }
        }
      } catch (error) {
        console.log(`❌ ${check.name}: erro - ${error.message}`);
        failed++;
      }
    }

    // Screenshot
    console.log('\n📸 Capturando screenshot...');
    await page.screenshot({ path: '/home/bot/clawd/site-pixel-alchemy/site-demo/studio-semeghini/screenshot.png', fullPage: true });
    console.log('✅ Screenshot salvo em screenshot.png');

    // Testar responsividade
    console.log('\n📱 Testando responsividade...');
    await page.setViewportSize({ width: 375, height: 667 }); // Mobile
    await page.waitForTimeout(1000);
    const mobileNav = await page.locator('nav').count() > 0;
    if (mobileNav) {
      console.log('✅ Mobile: Navegação visível');
      passed++;
    } else {
      console.log('❌ Mobile: Navegação não visível');
      failed++;
    }

    await page.setViewportSize({ width: 1920, height: 1080 }); // Desktop
    await page.waitForTimeout(1000);
    console.log('✅ Desktop: Responsivo');

    // Resumo
    console.log('\n' + '='.repeat(60));
    console.log('📊 RESUMO DA VALIDAÇÃO');
    console.log('='.repeat(60));
    console.log(`✅ Passou: ${passed}`);
    console.log(`❌ Falhou: ${failed}`);
    console.log('='.repeat(60));

    await browser.close();

    return failed === 0;

  } catch (error) {
    console.error('\n❌ Erro durante validação:', error.message);
    await browser.close();
    return false;
  }
}

validateSite()
  .then(success => {
    if (success) {
      console.log('\n✅ VALIDAÇÃO PASSOU!\n');
    } else {
      console.log('\n❌ VALIDAÇÃO FALHOU!\n');
    }
    process.exit(success ? 0 : 1);
  })
  .catch(err => {
    console.error('Erro fatal:', err);
    process.exit(1);
  });

// WhatsApp Float Button for Studio Test
document.addEventListener('DOMContentLoaded', function() {
    // Create WhatsApp button
    const whatsappButton = document.createElement('a');

    // Styling
    whatsappButton.href = 'https://wa.me/55000000000?text=Ol%C3%A1!%20Gostaria%20de%20agendar%20um%20hor%C3%A1rio';
    whatsappButton.target = '_blank';
    whatsappButton.className = 'whatsapp-float-button';

    // Add icon
    const icon = document.createElement('span');
    icon.innerHTML = '📱';
    icon.className = 'whatsapp-icon';

    whatsappButton.appendChild(icon);

    // Add to body
    document.body.appendChild(whatsappButton);

    // Show/hide on scroll
    let lastScrollTop = 0;
    window.addEventListener('scroll', function() {
        const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (currentScrollTop > 300) {
            whatsappButton.classList.add('visible');
        } else if (currentScrollTop < 100) {
            whatsappButton.classList.remove('visible');
        }

        lastScrollTop = currentScrollTop;
    });

    // Close button
    const closeButton = document.createElement('button');
    closeButton.innerHTML = '×';
    closeButton.className = 'whatsapp-close-button';
    closeButton.setAttribute('aria-label', 'Fechar WhatsApp');

    whatsappButton.appendChild(closeButton);

    closeButton.addEventListener('click', function(e) {
        e.preventDefault();
        whatsappButton.classList.remove('visible');
    });
});

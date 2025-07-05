// Welcome page animations and interactions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize typewriter animation
    initTypewriter();

    // Initialize GIF animation
    initGifAnimation();
});

function initTypewriter() {
    const typewriterElement = document.querySelector('.typewriter-text');

    if (!typewriterElement) {
        console.log('Typewriter element not found');
        return;
    }

    const text = typewriterElement.textContent;
    typewriterElement.textContent = '';
    typewriterElement.style.borderRight = '2px solid var(--green-color)';
    typewriterElement.style.animation = 'blink 1s infinite';

    let i = 0;
    function typeWriter() {
        if (i < text.length) {
            typewriterElement.textContent += text.charAt(i);
            i++;
            setTimeout(typeWriter, 100); // Adjust speed here
        } else {
            // Animation complete, remove cursor after a delay
            setTimeout(function() {
                typewriterElement.style.borderRight = 'none';
                typewriterElement.style.animation = 'none';
            }, 1000);
        }
    }

    // Start typing animation after a short delay
    setTimeout(typeWriter, 500);
}

function initGifAnimation() {
    const gif = document.getElementById('growth-gif');

    if (!gif) {
        console.log('Growth GIF element not found');
        return;
    }

    // Check if staticImagePath is available
    if (typeof staticImagePath === 'undefined') {
        console.log('staticImagePath not defined');
        return;
    }

    // Change GIF to static image after typewriter completes
    setTimeout(function() {
        gif.src = staticImagePath;
        console.log('GIF changed to static image');
    }, 4000); // Adjust timing based on typewriter duration
}

// Add CSS for blinking cursor animation
const style = document.createElement('style');
style.textContent = `
    @keyframes blink {
        0%, 50% { border-color: var(--green-color); }
        51%, 100% { border-color: transparent; }
    }
`;
document.head.appendChild(style);

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  corePlugins: {
    preflight: false
  },
  theme: {
    extend: {
      colors: {
        'vault-bg': '#0A0A0B',
        'vault-panel': '#111113',
        'vault-border': 'rgba(0,229,255,0.13)',
        cyan: '#00E5FF',
        amber: '#FFB400',
        success: '#00E676',
        danger: '#FF1744',
        'text-primary': '#E8EAF0',
        'text-muted': '#5A5F6E'
      },
      fontFamily: {
        display: ['Syne Mono', 'monospace'],
        body: ['DM Sans', 'sans-serif']
      },
      boxShadow: {
        cyan: '0 0 28px rgba(0, 229, 255, 0.2)',
        amber: '0 0 30px rgba(255, 180, 0, 0.25)',
        danger: '0 0 26px rgba(255, 23, 68, 0.2)'
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' }
        },
        gridDrift: {
          '0%': { backgroundPosition: '0 0, 0 0' },
          '100%': { backgroundPosition: '48px 48px, 48px 48px' }
        },
        blink: {
          '0%, 45%': { opacity: '1' },
          '46%, 100%': { opacity: '0' }
        }
      },
      animation: {
        scan: 'scan 7s linear infinite',
        grid: 'gridDrift 14s linear infinite',
        blink: 'blink 1s steps(1) infinite'
      }
    }
  },
  plugins: []
};

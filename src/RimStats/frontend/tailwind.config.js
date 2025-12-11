/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'rimworld': {
                    green: '#4ade80',
                    yellow: '#fbbf24',
                    red: '#ef4444',
                    blue: '#3b82f6',
                }
            }
        },
    },
    plugins: [],
}

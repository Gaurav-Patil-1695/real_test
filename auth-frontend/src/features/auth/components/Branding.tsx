import React from 'react';

function Branding() {
  return (
    <div className="branding">
      <div className="branding__logo" aria-hidden="true">
        <svg
          width="40"
          height="40"
          viewBox="0 0 40 40"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="branding__logo-icon"
        >
          <rect width="40" height="40" rx="10" fill="var(--color-accent-primary)" />
          <path
            d="M20 10C14.477 10 10 14.477 10 20C10 25.523 14.477 30 20 30C25.523 30 30 25.523 30 20C30 14.477 25.523 10 20 10ZM20 14C22.21 14 24 15.79 24 18C24 20.21 22.21 22 20 22C17.79 22 16 20.21 16 18C16 15.79 17.79 14 20 14ZM20 28C17.33 28 14.96 26.67 13.5 24.61C13.54 22.55 17.67 21.4 20 21.4C22.32 21.4 26.46 22.55 26.5 24.61C25.04 26.67 22.67 28 20 28Z"
            fill="var(--color-text-on-accent)"
          />
        </svg>
      </div>
      <span className="branding__wordmark">AuthStarter</span>
    </div>
  );
}

export default Branding;

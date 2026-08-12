/**
 * Unit tests for tokens.css and auth.css
 *
 * These tests load the CSS files as plain text and verify:
 *  - All expected CSS custom properties (design tokens) are declared
 *  - All expected class selectors are present
 *  - Token values match the spec
 *  - auth.css references tokens (var(--...)) rather than hard-coded values where applicable
 *
 * Test runner: Node built-in `node:test` + `node:assert` (most common convention
 * when no test framework is declared in package.json for a plain JS/CSS project).
 */

import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

const __dirname = dirname(fileURLToPath(import.meta.url));

const tokensCSS = readFileSync(
  resolve(__dirname, 'tokens.css'),
  'utf8'
);

const authCSS = readFileSync(
  resolve(__dirname, 'auth.css'),
  'utf8'
);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Extract the value of a CSS custom property from a CSS string.
 * Returns the trimmed raw value string, or undefined if not found.
 */
function getCSSVarValue(css, varName) {
  // Matches: --varName: <value>;
  const re = new RegExp(`${varName}\\s*:\\s*([^;]+);`);
  const m = css.match(re);
  return m ? m[1].trim() : undefined;
}

/**
 * Returns true if the given CSS string contains a declaration for varName.
 */
function hasCSSVar(css, varName) {
  return getCSSVarValue(css, varName) !== undefined;
}

/**
 * Returns true if the selector string appears in the CSS text.
 */
function hasSelector(css, selector) {
  // Escape special CSS selector characters for use in a plain search
  return css.includes(selector);
}

// ---------------------------------------------------------------------------
// tokens.css — design token declarations
// ---------------------------------------------------------------------------

describe('tokens.css — accent color tokens', () => {
  const accentTokens = {
    '--color-accent-primary': '#4f46e5',
    '--color-accent-primary-hover': '#4338ca',
    '--color-accent-primary-active': '#3730a3',
    '--color-accent-primary-subtle': '#eef2ff',
  };

  for (const [token, expectedValue] of Object.entries(accentTokens)) {
    it(`declares ${token} with value ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token), `Token ${token} not found`);
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }
});

describe('tokens.css — neutral color tokens', () => {
  const neutralTokens = {
    '--color-neutral-0': '#ffffff',
    '--color-neutral-50': '#f9fafb',
    '--color-neutral-100': '#f3f4f6',
    '--color-neutral-200': '#e5e7eb',
    '--color-neutral-300': '#d1d5db',
    '--color-neutral-400': '#9ca3af',
    '--color-neutral-500': '#6b7280',
    '--color-neutral-600': '#4b5563',
    '--color-neutral-700': '#374151',
    '--color-neutral-800': '#1f2937',
    '--color-neutral-900': '#111827',
  };

  for (const [token, expectedValue] of Object.entries(neutralTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token), `Token ${token} not found`);
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }
});

describe('tokens.css — semantic color tokens', () => {
  const semanticTokens = {
    '--color-error': '#dc2626',
    '--color-error-subtle': '#fef2f2',
    '--color-error-border': '#fca5a5',
    '--color-success': '#16a34a',
    '--color-success-subtle': '#f0fdf4',
    '--color-success-border': '#86efac',
    '--color-warning': '#d97706',
    '--color-warning-subtle': '#fffbeb',
    '--color-warning-border': '#fcd34d',
    '--color-info': '#2563eb',
    '--color-info-subtle': '#eff6ff',
    '--color-info-border': '#93c5fd',
  };

  for (const [token, expectedValue] of Object.entries(semanticTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token), `Token ${token} not found`);
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }
});

describe('tokens.css — background color tokens', () => {
  const bgTokens = {
    '--color-bg-page': '#f3f4f6',
    '--color-bg-card': '#ffffff',
    '--color-bg-input': '#ffffff',
    '--color-bg-input-disabled': '#f9fafb',
  };

  for (const [token, expectedValue] of Object.entries(bgTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token));
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }
});

describe('tokens.css — text color tokens', () => {
  const textTokens = {
    '--color-text-primary': '#111827',
    '--color-text-secondary': '#4b5563',
    '--color-text-placeholder': '#9ca3af',
    '--color-text-disabled': '#9ca3af',
    '--color-text-inverse': '#ffffff',
    '--color-text-link': '#4f46e5',
    '--color-text-link-hover': '#4338ca',
    '--color-text-error': '#dc2626',
    '--color-text-success': '#16a34a',
  };

  for (const [token, expectedValue] of Object.entries(textTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token));
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }
});

describe('tokens.css — border color tokens', () => {
  const borderColorTokens = {
    '--color-border-default': '#d1d5db',
    '--color-border-focus': '#4f46e5',
    '--color-border-error': '#dc2626',
    '--color-border-success': '#16a34a',
  };

  for (const [token, expectedValue] of Object.entries(borderColorTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token));
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }
});

describe('tokens.css — strength meter color tokens', () => {
  const strengthTokens = {
    '--color-strength-0': '#e5e7eb',
    '--color-strength-1': '#dc2626',
    '--color-strength-2': '#d97706',
    '--color-strength-3': '#2563eb',
    '--color-strength-4': '#16a34a',
  };

  for (const [token, expectedValue] of Object.entries(strengthTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token));
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }
});

describe('tokens.css — typography tokens', () => {
  it('declares --font-family-base containing Inter', () => {
    const val = getCSSVarValue(tokensCSS, '--font-family-base');
    assert.ok(val, '--font-family-base not found');
    assert.ok(val.includes('Inter'), `Expected Inter in font stack, got: ${val}`);
  });

  it('declares --font-family-mono containing JetBrains Mono', () => {
    const val = getCSSVarValue(tokensCSS, '--font-family-mono');
    assert.ok(val, '--font-family-mono not found');
    assert.ok(val.includes('JetBrains Mono'));
  });

  const fontSizeTokens = {
    '--font-size-xs': '0.75rem',
    '--font-size-sm': '0.875rem',
    '--font-size-md': '1rem',
    '--font-size-lg': '1.125rem',
    '--font-size-xl': '1.25rem',
    '--font-size-2xl': '1.5rem',
    '--font-size-3xl': '1.875rem',
  };

  for (const [token, expectedValue] of Object.entries(fontSizeTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token));
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }

  const fontWeightTokens = {
    '--font-weight-regular': '400',
    '--font-weight-medium': '500',
    '--font-weight-semibold': '600',
    '--font-weight-bold': '700',
  };

  for (const [token, expectedValue] of Object.entries(fontWeightTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token));
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }

  const lineHeightTokens = {
    '--line-height-tight': '1.25',
    '--line-height-snug': '1.375',
    '--line-height-normal': '1.5',
    '--line-height-relaxed': '1.625',
  };

  for (const [token, expectedValue] of Object.entries(lineHeightTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token));
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }

  const letterSpacingTokens = {
    '--letter-spacing-tight': '-0.025em',
    '--letter-spacing-normal': '0em',
    '--letter-spacing-wide': '0.025em',
    '--letter-spacing-wider': '0.05em',
  };

  for (const [token, expectedValue] of Object.entries(letterSpacingTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token));
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }
});

describe('tokens.css — spacing tokens', () => {
  const spacingTokens = {
    '--spacing-0': '0rem',
    '--spacing-1': '0.25rem',
    '--spacing-2': '0.5rem',
    '--spacing-3': '0.75rem',
    '--spacing-4': '1rem',
    '--spacing-5': '1.25rem',
    '--spacing-6': '1.5rem',
    '--spacing-8': '2rem',
    '--spacing-10': '2.5rem',
    '--spacing-12': '3rem',
    '--spacing-16': '4rem',
    '--spacing-20': '5rem',
    '--spacing-24': '6rem',
  };

  for (const [token, expectedValue] of Object.entries(spacingTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token));
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }
});

describe('tokens.css — border radius tokens', () => {
  const radiusTokens = {
    '--radius-none': '0px',
    '--radius-sm': '0.125rem',
    '--radius-md': '0.375rem',
    '--radius-lg': '0.5rem',
    '--radius-xl': '0.75rem',
    '--radius-2xl': '1rem',
    '--radius-full': '9999px',
  };

  for (const [token, expectedValue] of Object.entries(radiusTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token));
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }
});

describe('tokens.css — border width tokens', () => {
  const borderWidthTokens = {
    '--border-width-thin': '1px',
    '--border-width-medium': '2px',
    '--border-width-thick': '4px',
  };

  for (const [token, expectedValue] of Object.entries(borderWidthTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token));
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }
});

describe('tokens.css — shadow tokens', () => {
  it('declares --shadow-sm', () => assert.ok(hasCSSVar(tokensCSS, '--shadow-sm')));
  it('declares --shadow-md', () => assert.ok(hasCSSVar(tokensCSS, '--shadow-md')));
  it('declares --shadow-lg', () => assert.ok(hasCSSVar(tokensCSS, '--shadow-lg')));
  it('declares --shadow-xl', () => assert.ok(hasCSSVar(tokensCSS, '--shadow-xl')));
  it('declares --shadow-inner', () => assert.ok(hasCSSVar(tokensCSS, '--shadow-inner')));
  it('--shadow-none is none', () => {
    assert.equal(getCSSVarValue(tokensCSS, '--shadow-none'), 'none');
  });
});

describe('tokens.css — transition tokens', () => {
  const transitionTokens = {
    '--transition-duration-fast': '100ms',
    '--transition-duration-base': '150ms',
    '--transition-duration-slow': '200ms',
    '--transition-duration-slower': '300ms',
  };

  for (const [token, expectedValue] of Object.entries(transitionTokens)) {
    it(`declares ${token} = ${expectedValue}`, () => {
      assert.ok(hasCSSVar(tokensCSS, token));
      assert.equal(getCSSVarValue(tokensCSS, token), expectedValue);
    });
  }

  it('declares --transition-easing-default as cubic-bezier', () => {
    const val = getCSSVarValue(tokensCSS, '--transition-easing-default');
    assert.ok(val && val.includes('cubic-bezier'));
  });

  it('declares --transition-easing-in as cubic-bezier', () => {
    const val = getCSSVarValue(tokensCSS, '--transition-easing-in');
    assert.ok(val && val.includes('cubic-bezier'));
  });

  it('declares --transition-easing-out as cubic-bezier', () => {
    const val = getCSSVarValue(tokensCSS, '--transition-easing-out');
    assert.ok(val && val.includes('cubic-bezier'));
  });
});

describe('tokens.css — layout / card tokens', () => {
  it('declares --card-width = 28rem', () => {
    assert.equal(getCSSVarValue(tokensCSS, '--card-width'), '28rem');
  });

  it('--card-padding references --spacing-8 via var()', () => {
    const val = getCSSVarValue(tokensCSS, '--card-padding');
    assert.ok(val && val.includes('var(--spacing-8)'));
  });

  it('--card-border-radius references --radius-xl via var()', () => {
    const val = getCSSVarValue(tokensCSS, '--card-border-radius');
    assert.ok(val && val.includes('var(--radius-xl)'));
  });

  it('--card-shadow references --shadow-lg via var()', () => {
    const val = getCSSVarValue(tokensCSS, '--card-shadow');
    assert.ok(val && val.includes('var(--shadow-lg)'));
  });

  it('--card-bg references --color-bg-card via var()', () => {
    const val = getCSSVarValue(tokensCSS, '--card-bg');
    assert.ok(val && val.includes('var(--color-bg-card)'));
  });
});

describe('tokens.css — layout / input tokens', () => {
  it('declares --input-height = 2.5rem', () => {
    assert.equal(getCSSVarValue(tokensCSS, '--input-height'), '2.5rem');
  });

  it('--input-padding-x references --spacing-3', () => {
    const val = getCSSVarValue(tokensCSS, '--input-padding-x');
    assert.ok(val && val.includes('var(--spacing-3)'));
  });

  it('--input-padding-y references --spacing-2', () => {
    const val = getCSSVarValue(tokensCSS, '--input-padding-y');
    assert.ok(val && val.includes('var(--spacing-2)'));
  });

  it('--input-border-radius references --radius-md', () => {
    const val = getCSSVarValue(tokensCSS, '--input-border-radius');
    assert.ok(val && val.includes('var(--radius-md)'));
  });

  it('--input-border-color references --color-border-default', () => {
    const val = getCSSVarValue(tokensCSS, '--input-border-color');
    assert.ok(val && val.includes('var(--color-border-default)'));
  });

  it('--input-focus-ring-width references --border-width-medium', () => {
    const val = getCSSVarValue(tokensCSS, '--input-focus-ring-width');
    assert.ok(val && val.includes('var(--border-width-medium)'));
  });

  it('--input-focus-ring-color references --color-border-focus', () => {
    const val = getCSSVarValue(tokensCSS, '--input-focus-ring-color');
    assert.ok(val && val.includes('var(--color-border-focus)'));
  });
});

describe('tokens.css — layout / button tokens', () => {
  it('declares --button-height = 2.5rem', () => {
    assert.equal(getCSSVarValue(tokensCSS, '--button-height'), '2.5rem');
  });

  it('--button-padding-x references --spacing-4', () => {
    const val = getCSSVarValue(tokensCSS, '--button-padding-x');
    assert.ok(val && val.includes('var(--spacing-4)'));
  });

  it('--button-border-radius references --radius-md', () => {
    const val = getCSSVarValue(tokensCSS, '--button-border-radius');
    assert.ok(val && val.includes('var(--radius-md)'));
  });

  it('--button-font-weight references --font-weight-semibold', () => {
    const val = getCSSVarValue(tokensCSS, '--button-font-weight');
    assert.ok(val && val.includes('var(--font-weight-semibold)'));
  });
});

describe('tokens.css — branding tokens', () => {
  it('declares --brand-logo-size = 2.5rem', () => {
    assert.equal(getCSSVarValue(tokensCSS, '--brand-logo-size'), '2.5rem');
  });

  it('--brand-gap references --spacing-3', () => {
    const val = getCSSVarValue(tokensCSS, '--brand-gap');
    assert.ok(val && val.includes('var(--spacing-3)'));
  });
});

describe('tokens.css — :root scope', () => {
  it('all tokens are declared inside :root block', () => {
    assert.ok(tokensCSS.includes(':root'), 'file should contain :root selector');
    // Very simple check: the first occurrence of :root opens before token declarations
    const rootIndex = tokensCSS.indexOf(':root');
    const firstTokenIndex = tokensCSS.indexOf('--color-accent-primary');
    assert.ok(rootIndex < firstTokenIndex, ':root should precede token declarations');
  });
});

// ---------------------------------------------------------------------------
// auth.css — class selectors present
// ---------------------------------------------------------------------------

describe('auth.css — page & card selectors', () => {
  const selectors = [
    '.auth-page',
    '.auth-card',
    '.auth-card__branding',
    '.auth-card__header',
    '.auth-card__title',
    '.auth-card__subtitle',
    '.auth-card__body',
    '.auth-card__footer',
    '.auth-card__footer-row',
  ];

  for (const selector of selectors) {
    it(`contains selector ${selector}`, () => {
      assert.ok(hasSelector(authCSS, selector), `Selector ${selector} not found`);
    });
  }
});

describe('auth.css — branding selectors', () => {
  const selectors = ['.branding', '.branding__logo', '.branding__logo-icon', '.branding__name'];

  for (const selector of selectors) {
    it(`contains selector ${selector}`, () => {
      assert.ok(hasSelector(authCSS, selector));
    });
  }
});

describe('auth.css — form field selectors', () => {
  const selectors = [
    '.auth-card__field',
    '.field__label',
    '.field__label--required',
    '.field__input-wrapper',
    '.field__input',
    '.field__input::placeholder',
    '.field__input:focus',
    '.field__input:disabled',
    '.field__input--error',
    '.field__input--success',
    '.field__input--with-toggle',
    '.field__toggle',
    '.field__toggle:hover',
    '.field__toggle:focus-visible',
    '.field__toggle:disabled',
    '.field__toggle-icon',
    '.field__error',
    '.field__error-icon',
    '.field__hint',
  ];

  for (const selector of selectors) {
    it(`contains selector ${selector}`, () => {
      assert.ok(hasSelector(authCSS, selector));
    });
  }
});

describe('auth.css — checkbox selectors', () => {
  const selectors = [
    '.checkbox',
    '.checkbox__input',
    '.checkbox__input:disabled',
    '.checkbox__label',
    '.checkbox__label a',
    '.checkbox__label a:hover',
  ];

  for (const selector of selectors) {
    it(`contains selector ${selector}`, () => {
      assert.ok(hasSelector(authCSS, selector));
    });
  }
});

describe('auth.css — button selectors', () => {
  const selectors = [
    '.btn',
    '.btn--primary',
    '.btn--full-width',
    '.btn--loading',
    '.btn__spinner',
    '.btn--link',
    '.btn--link:hover',
    '.btn--link:focus-visible',
    '.auth-link',
    '.auth-link:hover',
    '.auth-link:focus-visible',
  ];

  for (const selector of selectors) {
    it(`contains selector ${selector}`, () => {
      assert.ok(hasSelector(authCSS, selector));
    });
  }
});

describe('auth.css — alert selectors', () => {
  const selectors = [
    '.alert',
    '.alert__icon',
    '.alert__content',
    '.alert__title',
    '.alert__message',
    '.alert--error',
    '.alert--success',
    '.alert--warning',
    '.alert--info',
  ];

  for (const selector of selectors) {
    it(`contains selector ${selector}`, () => {
      assert.ok(hasSelector(authCSS, selector));
    });
  }
});

describe('auth.css — strength meter selectors', () => {
  const selectors = [
    '.strength-meter',
    '.strength-meter__track',
    '.strength-meter__segment',
    '.strength-meter__segment--active-1',
    '.strength-meter__segment--active-2',
    '.strength-meter__segment--active-3',
    '.strength-meter__segment--active-4',
    '.strength-meter__footer',
    '.strength-meter__label',
    '.strength-meter__label--1',
    '.strength-meter__label--2',
    '.strength-meter__label--3',
    '.strength-meter__label--4',
    '.strength-meter__rules',
    '.strength-meter__rule',
    '.strength-meter__rule--met',
    '.strength-meter__rule-icon',
  ];

  for (const selector of selectors) {
    it(`contains selector ${selector}`, () => {
      assert.ok(hasSelector(authCSS, selector));
    });
  }
});

describe('auth.css — divider and misc selectors', () => {
  const selectors = ['.auth-divider', '.auth-card__field-row'];

  for (const selector of selectors) {
    it(`contains selector ${selector}`, () => {
      assert.ok(hasSelector(authCSS, selector));
    });
  }
});

describe('auth.css — responsive media queries', () => {
  it('has a max-width: 32rem breakpoint', () => {
    assert.ok(authCSS.includes('max-width: 32rem'));
  });

  it('has a max-width: 24rem breakpoint', () => {
    assert.ok(authCSS.includes('max-width: 24rem'));
  });

  it('has a max-height: 36rem breakpoint', () => {
    assert.ok(authCSS.includes('max-height: 36rem'));
  });
});

describe('auth.css — uses design tokens via var()', () => {
  it('references var(--color-bg-page) in .auth-page', () => {
    assert.ok(authCSS.includes('var(--color-bg-page)'));
  });

  it('references var(--card-width)', () => {
    assert.ok(authCSS.includes('var(--card-width)'));
  });

  it('references var(--card-padding)', () => {
    assert.ok(authCSS.includes('var(--card-padding)'));
  });

  it('references var(--card-border-radius)', () => {
    assert.ok(authCSS.includes('var(--card-border-radius)'));
  });

  it('references var(--input-height)', () => {
    assert.ok(authCSS.includes('var(--input-height)'));
  });

  it('references var(--input-border-color)', () => {
    assert.ok(authCSS.includes('var(--input-border-color)'));
  });

  it('references var(--color-accent-primary) for branding logo bg', () => {
    assert.ok(authCSS.includes('var(--color-accent-primary)'));
  });

  it('references var(--color-error-subtle) for alert--error bg', () => {
    assert.ok(authCSS.includes('var(--color-error-subtle)'));
  });

  it('references var(--color-strength-0) for default segment color', () => {
    assert.ok(authCSS.includes('var(--color-strength-0)'));
  });

  it('defines @keyframes auth-spin animation for spinner', () => {
    assert.ok(authCSS.includes('@keyframes auth-spin'));
  });
});

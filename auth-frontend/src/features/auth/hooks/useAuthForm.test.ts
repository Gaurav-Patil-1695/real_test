/**
 * Tests for useAuthForm hook.
 * Runner: Jest + @testing-library/react-hooks (most common convention for
 * React hook testing in projects without an explicit vitest config).
 */
import { renderHook, act } from '@testing-library/react-hooks';
import { useAuthForm, FieldValues, FieldErrors } from './useAuthForm';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

type SimpleForm = { email: string; password: string; remember: boolean };

const initialValues: SimpleForm = {
  email: '',
  password: '',
  remember: false,
};

/** No-op validator – returns no errors */
const noopValidate = (_values: SimpleForm): FieldErrors => ({});

/** Validator that always returns errors for every field */
const alwaysErrorValidate = (_values: SimpleForm): FieldErrors => ({
  email: 'Email is required',
  password: 'Password is required',
});

/** Validator that only fails when email is empty */
const emailRequiredValidate = (values: SimpleForm): FieldErrors => {
  const errors: FieldErrors = {};
  if (!values.email) errors.email = 'Email is required';
  return errors;
};

/** Creates a minimal synthetic ChangeEvent for an <input> */
function makeChangeEvent(
  name: string,
  value: string,
  type = 'text',
  checked = false
): React.ChangeEvent<HTMLInputElement> {
  return {
    target: { name, value, type, checked } as HTMLInputElement,
  } as React.ChangeEvent<HTMLInputElement>;
}

/** Creates a minimal synthetic FocusEvent for an <input> */
function makeBlurEvent(name: string): React.FocusEvent<HTMLInputElement> {
  return {
    target: { name } as HTMLInputElement,
  } as React.FocusEvent<HTMLInputElement>;
}

/** Creates a minimal synthetic FormEvent for a <form> */
function makeSubmitEvent(): React.FormEvent<HTMLFormElement> {
  return { preventDefault: jest.fn() } as unknown as React.FormEvent<HTMLFormElement>;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useAuthForm – initial state', () => {
  it('exposes the initial values unchanged', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    expect(result.current.values).toEqual(initialValues);
  });

  it('starts with no touched fields', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    expect(result.current.touched).toEqual({});
  });

  it('starts with isSubmitting = false', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    expect(result.current.isSubmitting).toBe(false);
  });

  it('starts with submitError = null', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    expect(result.current.submitError).toBeNull();
  });

  it('starts with submitSuccess = false', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    expect(result.current.submitSuccess).toBe(false);
  });

  it('derives errors from initial values on first render', () => {
    const { result } = renderHook(() =>
      useAuthForm({
        initialValues,
        validate: alwaysErrorValidate,
        onSubmit: jest.fn(),
      })
    );
    expect(result.current.errors).toEqual({
      email: 'Email is required',
      password: 'Password is required',
    });
  });
});

// ---------------------------------------------------------------------------

describe('useAuthForm – handleChange', () => {
  it('updates a text field value', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.handleChange(makeChangeEvent('email', 'user@example.com'));
    });
    expect(result.current.values.email).toBe('user@example.com');
  });

  it('updates a checkbox field (boolean)', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.handleChange(
        makeChangeEvent('remember', '', 'checkbox', true)
      );
    });
    expect(result.current.values.remember).toBe(true);
  });

  it('clears submitError on change', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.setSubmitError('Some error');
    });
    act(() => {
      result.current.handleChange(makeChangeEvent('email', 'a@b.com'));
    });
    expect(result.current.submitError).toBeNull();
  });

  it('clears submitSuccess on change', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit })
    );
    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(result.current.submitSuccess).toBe(true);

    act(() => {
      result.current.handleChange(makeChangeEvent('email', 'x@y.com'));
    });
    expect(result.current.submitSuccess).toBe(false);
  });
});

// ---------------------------------------------------------------------------

describe('useAuthForm – handleBlur', () => {
  it('marks a field as touched', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.handleBlur(makeBlurEvent('email'));
    });
    expect(result.current.touched.email).toBe(true);
  });

  it('does not touch other fields', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.handleBlur(makeBlurEvent('email'));
    });
    expect(result.current.touched.password).toBeUndefined();
  });

  it('can mark multiple fields as touched independently', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.handleBlur(makeBlurEvent('email'));
      result.current.handleBlur(makeBlurEvent('password'));
    });
    expect(result.current.touched).toEqual({ email: true, password: true });
  });
});

// ---------------------------------------------------------------------------

describe('useAuthForm – handleSubmit (validation failures)', () => {
  it('calls preventDefault on the event', () => {
    const event = makeSubmitEvent();
    const { result } = renderHook(() =>
      useAuthForm({
        initialValues,
        validate: alwaysErrorValidate,
        onSubmit: jest.fn(),
      })
    );
    act(() => {
      result.current.handleSubmit(event);
    });
    expect((event as any).preventDefault).toHaveBeenCalledTimes(1);
  });

  it('marks all fields touched when submit is attempted', () => {
    const { result } = renderHook(() =>
      useAuthForm({
        initialValues,
        validate: alwaysErrorValidate,
        onSubmit: jest.fn(),
      })
    );
    act(() => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(result.current.touched).toEqual({
      email: true,
      password: true,
      remember: true,
    });
  });

  it('does NOT call onSubmit when validation fails', () => {
    const onSubmit = jest.fn();
    const { result } = renderHook(() =>
      useAuthForm({
        initialValues,
        validate: alwaysErrorValidate,
        onSubmit,
      })
    );
    act(() => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('keeps isSubmitting = false when validation fails', () => {
    const { result } = renderHook(() =>
      useAuthForm({
        initialValues,
        validate: alwaysErrorValidate,
        onSubmit: jest.fn(),
      })
    );
    act(() => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(result.current.isSubmitting).toBe(false);
  });
});

// ---------------------------------------------------------------------------

describe('useAuthForm – handleSubmit (successful submit)', () => {
  it('calls onSubmit with current values', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    const filledValues: SimpleForm = {
      email: 'user@example.com',
      password: 'secret',
      remember: false,
    };
    const { result } = renderHook(() =>
      useAuthForm({
        initialValues: filledValues,
        validate: noopValidate,
        onSubmit,
      })
    );
    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(onSubmit).toHaveBeenCalledWith(filledValues);
  });

  it('sets submitSuccess = true after successful onSubmit', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit })
    );
    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(result.current.submitSuccess).toBe(true);
  });

  it('leaves submitError = null after successful onSubmit', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit })
    );
    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(result.current.submitError).toBeNull();
  });

  it('resets isSubmitting to false after successful onSubmit', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit })
    );
    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(result.current.isSubmitting).toBe(false);
  });
});

// ---------------------------------------------------------------------------

describe('useAuthForm – handleSubmit (failed submit)', () => {
  it('sets submitError to the thrown Error message', async () => {
    const onSubmit = jest.fn().mockRejectedValue(new Error('Network failure'));
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit })
    );
    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(result.current.submitError).toBe('Network failure');
  });

  it('sets a fallback message for non-Error throws', async () => {
    const onSubmit = jest.fn().mockRejectedValue('plain string error');
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit })
    );
    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(result.current.submitError).toBe('An unexpected error occurred.');
  });

  it('keeps submitSuccess = false after a failed onSubmit', async () => {
    const onSubmit = jest.fn().mockRejectedValue(new Error('oops'));
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit })
    );
    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(result.current.submitSuccess).toBe(false);
  });

  it('resets isSubmitting to false after a failed onSubmit', async () => {
    const onSubmit = jest.fn().mockRejectedValue(new Error('oops'));
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit })
    );
    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(result.current.isSubmitting).toBe(false);
  });
});

// ---------------------------------------------------------------------------

describe('useAuthForm – setFieldValue', () => {
  it('updates a named field value', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.setFieldValue('email', 'direct@test.com');
    });
    expect(result.current.values.email).toBe('direct@test.com');
  });

  it('can set a boolean field value', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.setFieldValue('remember', true);
    });
    expect(result.current.values.remember).toBe(true);
  });

  it('clears submitError', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.setSubmitError('previous error');
    });
    act(() => {
      result.current.setFieldValue('email', 'x@y.com');
    });
    expect(result.current.submitError).toBeNull();
  });

  it('clears submitSuccess', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit })
    );
    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(result.current.submitSuccess).toBe(true);
    act(() => {
      result.current.setFieldValue('email', 'new@value.com');
    });
    expect(result.current.submitSuccess).toBe(false);
  });
});

// ---------------------------------------------------------------------------

describe('useAuthForm – setSubmitError', () => {
  it('sets a custom error message', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.setSubmitError('Custom error');
    });
    expect(result.current.submitError).toBe('Custom error');
  });

  it('can clear a previously set error by passing null', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.setSubmitError('Some error');
    });
    act(() => {
      result.current.setSubmitError(null);
    });
    expect(result.current.submitError).toBeNull();
  });
});

// ---------------------------------------------------------------------------

describe('useAuthForm – reset', () => {
  it('restores values to initialValues', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.handleChange(makeChangeEvent('email', 'changed@test.com'));
    });
    act(() => {
      result.current.reset();
    });
    expect(result.current.values).toEqual(initialValues);
  });

  it('clears all touched flags', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.handleBlur(makeBlurEvent('email'));
      result.current.handleBlur(makeBlurEvent('password'));
    });
    act(() => {
      result.current.reset();
    });
    expect(result.current.touched).toEqual({});
  });

  it('clears submitError', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.setSubmitError('Some error');
    });
    act(() => {
      result.current.reset();
    });
    expect(result.current.submitError).toBeNull();
  });

  it('clears submitSuccess', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit })
    );
    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });
    expect(result.current.submitSuccess).toBe(true);
    act(() => {
      result.current.reset();
    });
    expect(result.current.submitSuccess).toBe(false);
  });

  it('sets isSubmitting back to false', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate: noopValidate, onSubmit: jest.fn() })
    );
    act(() => {
      result.current.reset();
    });
    expect(result.current.isSubmitting).toBe(false);
  });
});

// ---------------------------------------------------------------------------

describe('useAuthForm – live error derivation', () => {
  it('re-derives errors when field values change', () => {
    const { result } = renderHook(() =>
      useAuthForm({
        initialValues,
        validate: emailRequiredValidate,
        onSubmit: jest.fn(),
      })
    );
    // Initially email is empty => error expected
    expect(result.current.errors.email).toBe('Email is required');

    act(() => {
      result.current.handleChange(makeChangeEvent('email', 'user@example.com'));
    });
    // After filling email => no error
    expect(result.current.errors.email).toBeUndefined();
  });
});

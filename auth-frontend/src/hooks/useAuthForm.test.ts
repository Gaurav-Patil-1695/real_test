import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAuthForm } from './useAuthForm';

describe('useAuthForm', () => {
  it('initializes with provided initial values', () => {
    const { result } = renderHook(() =>
      useAuthForm({ email: '', password: '' })
    );
    expect(result.current.values).toEqual({ email: '', password: '' });
  });

  it('updates a field value on change', () => {
    const { result } = renderHook(() =>
      useAuthForm({ email: '', password: '' })
    );
    act(() => {
      result.current.handleChange({
        target: { name: 'email', value: 'user@example.com' },
      } as React.ChangeEvent<HTMLInputElement>);
    });
    expect(result.current.values.email).toBe('user@example.com');
  });

  it('updates password field independently', () => {
    const { result } = renderHook(() =>
      useAuthForm({ email: '', password: '' })
    );
    act(() => {
      result.current.handleChange({
        target: { name: 'password', value: 'secret123' },
      } as React.ChangeEvent<HTMLInputElement>);
    });
    expect(result.current.values.password).toBe('secret123');
    expect(result.current.values.email).toBe('');
  });

  it('exposes errors object (initially empty or undefined)', () => {
    const { result } = renderHook(() =>
      useAuthForm({ email: '' })
    );
    expect(result.current.errors).toBeDefined();
  });

  it('handles multiple fields', () => {
    const { result } = renderHook(() =>
      useAuthForm({ email: '', password: '', confirmPassword: '' })
    );
    act(() => {
      result.current.handleChange({
        target: { name: 'confirmPassword', value: 'abc' },
      } as React.ChangeEvent<HTMLInputElement>);
    });
    expect(result.current.values.confirmPassword).toBe('abc');
  });

  it('does not mutate other fields when one changes', () => {
    const { result } = renderHook(() =>
      useAuthForm({ email: 'a@b.com', password: 'pass' })
    );
    act(() => {
      result.current.handleChange({
        target: { name: 'email', value: 'new@b.com' },
      } as React.ChangeEvent<HTMLInputElement>);
    });
    expect(result.current.values.password).toBe('pass');
  });
});

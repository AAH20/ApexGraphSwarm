/**
 * React component for chart tooltip.
 *
 * @module ChartTooltip
 * @packageDocumentation
 */
'use client';

import {cloneElement, useCallback, useEffect, useId, useRef, useState, type FocusEvent, type KeyboardEvent as ReactKeyboardEvent, type MouseEvent, type PointerEvent, type ReactElement} from 'react';
import {createPortal} from 'react-dom';
import styles from './ChartTooltip.module.css';

/**
 * Type ChartTooltipDetail.
 *
 *
 * @example
 * ```typescript
 * import { ChartTooltipDetail } from './module';
 * ```
 */
export type ChartTooltipDetail = {label: string; value: string};
export type ChartTooltipProps = {
  title: string;
  details: ChartTooltipDetail[];
  children: ReactElement<Record<string, unknown>>;
};
/**
 * Type Point.
 *
 *
 * @example
 * ```typescript
 * import { Point } from './module';
 * ```
 */
type Point = {x: number; y: number};

/** Wrap one HTML or SVG chart mark with an accessible, viewport-positioned detail tooltip. */
export default function ChartTooltip({title, details, children}: ChartTooltipProps) {
  const generatedId = useId();
  const tooltipId = `chart-tooltip-${generatedId}`;
  const anchor = useRef<Element | null>(null);
  const pointerOver = useRef(false);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);
  const [point, setPoint] = useState<Point>({x: 0, y: 0});
  const [position, setPosition] = useState<Point>({x: 12, y: 12});
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);
  const clearClose = useCallback(() => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    closeTimer.current = null;
  }, []);
  const track = useCallback((element: Element | null, event?: {clientX: number; clientY: number}, focus = false) => {
    anchor.current = element;
    const bounds = element?.getBoundingClientRect();
    setPoint({x: event?.clientX ?? (bounds ? bounds.left + bounds.width / 2 : 12), y: event?.clientY ?? (focus && bounds ? bounds.bottom : bounds ? bounds.top + bounds.height / 2 : 12)});
  }, []);
  const scheduleClose = useCallback(() => {
    clearClose();
    closeTimer.current = setTimeout(() => {
      if (!pinned) setOpen(false);
    }, 140);
  }, [clearClose, pinned]);

  useEffect(() => {
    if (!open) return;
    const dismiss = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') { setOpen(false); setPinned(false); }
    };
    const outside = (event: globalThis.PointerEvent) => {
      const target = event.target;
      if (pinned && target instanceof Node && !anchor.current?.contains(target) && !tooltipRef.current?.contains(target)) {
        setPinned(false);
        setOpen(false);
      }
    };
    const reposition = () => {
      const bounds = anchor.current?.getBoundingClientRect();
      if (bounds) setPoint(current => ({x: bounds.left + bounds.width / 2, y: bounds.bottom}));
    };
    window.addEventListener('keydown', dismiss);
    document.addEventListener('pointerdown', outside);
    window.addEventListener('resize', reposition);
    window.addEventListener('scroll', reposition, true);
    return () => {
      window.removeEventListener('keydown', dismiss);
      document.removeEventListener('pointerdown', outside);
      window.removeEventListener('resize', reposition);
      window.removeEventListener('scroll', reposition, true);
    };
  }, [open, pinned]);

  useEffect(() => {
    if (!open || !mounted) return;
    const panel = tooltipRef.current;
    if (!panel) return;
    const rect = panel.getBoundingClientRect();
    const margin = 12;
    const width = window.innerWidth;
    const height = window.innerHeight;
    let left = point.x + 14;
    if (left + rect.width > width - margin) left = point.x - rect.width - 14;
    left = Math.max(margin, Math.min(left, width - rect.width - margin));
    let top = point.y + 14;
    if (top + rect.height > height - margin) top = point.y - rect.height - 14;
    top = Math.max(margin, Math.min(top, height - rect.height - margin));
    setPosition({x: left, y: top});
  }, [open, mounted, point, title, details]);

  useEffect(() => () => { if (closeTimer.current) clearTimeout(closeTimer.current); }, []);

  const triggerProps = children.props as Record<string, unknown>;
  const existingPointerEnter = triggerProps.onPointerEnter as ((event: PointerEvent<Element>) => void) | undefined;
  const existingPointerMove = triggerProps.onPointerMove as ((event: PointerEvent<Element>) => void) | undefined;
  const existingPointerLeave = triggerProps.onPointerLeave as ((event: PointerEvent<Element>) => void) | undefined;
  const existingFocus = triggerProps.onFocus as ((event: FocusEvent<Element>) => void) | undefined;
  const existingBlur = triggerProps.onBlur as ((event: FocusEvent<Element>) => void) | undefined;
  const existingClick = triggerProps.onClick as ((event: MouseEvent<Element>) => void) | undefined;
  const existingKeyDown = triggerProps.onKeyDown as ((event: ReactKeyboardEvent<Element>) => void) | undefined;
  const nativeClickable = typeof children.type === 'string' && ['button', 'a', 'input', 'select', 'textarea'].includes(children.type);
  const describedBy = [typeof triggerProps['aria-describedby'] === 'string' ? triggerProps['aria-describedby'] : '', tooltipId].filter(Boolean).join(' ');
  const trigger = cloneElement(children, {
    tabIndex: typeof triggerProps.tabIndex === 'number' ? triggerProps.tabIndex : 0,
    'aria-describedby': describedBy,
    'aria-label': typeof triggerProps['aria-label'] === 'string' ? triggerProps['aria-label'] : title,
    className: [typeof triggerProps.className === 'string' ? triggerProps.className : '', styles.trigger].filter(Boolean).join(' '),
    onPointerEnter: (event: PointerEvent<Element>) => { existingPointerEnter?.(event); pointerOver.current = true; clearClose(); track(event.currentTarget, event); setOpen(true); },
    onPointerMove: (event: PointerEvent<Element>) => { existingPointerMove?.(event); track(event.currentTarget, event); },
    onPointerLeave: (event: PointerEvent<Element>) => { existingPointerLeave?.(event); pointerOver.current = false; scheduleClose(); },
    onFocus: (event: FocusEvent<Element>) => { existingFocus?.(event); clearClose(); track(event.currentTarget, undefined, true); setOpen(true); },
    onBlur: (event: FocusEvent<Element>) => { existingBlur?.(event); if (!pinned && !pointerOver.current) scheduleClose(); },
    onClick: (event: MouseEvent<Element>) => { existingClick?.(event); clearClose(); track(event.currentTarget, {clientX: event.clientX, clientY: event.clientY}); const nextPinned = !pinned; setPinned(nextPinned); setOpen(nextPinned); },
    onKeyDown: (event: ReactKeyboardEvent<Element>) => {
      existingKeyDown?.(event);
      if (!nativeClickable && (event.key === 'Enter' || event.key === ' ') && !event.repeat) {
        event.preventDefault();
        const nextPinned = !pinned;
        setPinned(nextPinned);
        setOpen(nextPinned);
      }
    },
  });

  const tooltip = mounted ? createPortal(
    <div
      ref={tooltipRef}
      id={tooltipId}
      role="tooltip"
      aria-hidden={!open}
      className={styles.tooltip}
      style={{left: position.x, top: position.y, visibility: open ? 'visible' : 'hidden'}}
      onPointerEnter={clearClose}
      onPointerLeave={scheduleClose}
      onClick={event => event.stopPropagation()}
    >
      <strong>{title}</strong>
      <dl>{details.map((detail, index) => <div key={`${detail.label}-${index}`}><dt>{detail.label}</dt><dd>{detail.value}</dd></div>)}</dl>
    </div>,
    document.body,
  ) : null;
  return <>{trigger}{tooltip}</>;
}

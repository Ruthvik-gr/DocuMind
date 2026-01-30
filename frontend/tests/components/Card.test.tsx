import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card } from '../../src/components/common/Card';

describe('Card Component', () => {
  it('renders children correctly', () => {
    render(<Card>Test Content</Card>);
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('applies default classes', () => {
    const { container } = render(<Card>Content</Card>);
    const cardDiv = container.firstChild as HTMLElement;
    expect(cardDiv).toHaveClass('bg-white');
    expect(cardDiv).toHaveClass('rounded-lg');
    expect(cardDiv).toHaveClass('shadow-md');
    expect(cardDiv).toHaveClass('p-6');
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="custom-class">Content</Card>);
    const cardDiv = container.firstChild as HTMLElement;
    expect(cardDiv).toHaveClass('custom-class');
    expect(cardDiv).toHaveClass('bg-white'); // Still has default classes
  });

  it('renders complex children', () => {
    render(
      <Card>
        <h1>Title</h1>
        <p>Description</p>
        <button>Action</button>
      </Card>
    );
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Description')).toBeInTheDocument();
    expect(screen.getByText('Action')).toBeInTheDocument();
  });
});

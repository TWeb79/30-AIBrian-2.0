import React from 'react';

export const ReflexPanel = ({ theme }) => {
  const style = {
    padding: 8,
    borderRadius: 6,
    background: theme?.surface ?? '#ffffff',
    color: theme?.textPrimary ?? '#000',
  };
  return (
    <div data-testid="reflex-panel" style={style}>
      Reflex Panel
    </div>
  );
};
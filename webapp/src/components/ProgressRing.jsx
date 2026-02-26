export default function ProgressRing({ percent = 0, size = 80, strokeWidth = 6, color = '#34d399', label }) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (Math.min(percent, 100) / 100) * circumference

  return (
    <div className="flex flex-col items-center relative">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#2d3748" strokeWidth={strokeWidth} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
      <span
        className="absolute text-sm font-bold text-text-primary"
        style={{ top: size / 2 - 9, left: '50%', transform: 'translateX(-50%)' }}
      >
        {Math.round(percent)}%
      </span>
      {label && <span className="text-xs text-text-secondary mt-1">{label}</span>}
    </div>
  )
}

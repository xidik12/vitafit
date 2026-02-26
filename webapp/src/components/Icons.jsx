/**
 * Outline SVG icons — replaces all emoji usage across the app.
 * Each icon is a pure SVG component accepting className and size props.
 */

const s = (d, vb = '0 0 24 24') => ({ className = 'w-5 h-5', ...props }) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox={vb} strokeWidth={1.5} stroke="currentColor" className={className} {...props}>
    {d}
  </svg>
)

// Navigation
export const HomeIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955a1.126 1.126 0 011.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />)

export const DumbbellIcon = s(<><path strokeLinecap="round" strokeLinejoin="round" d="M6.75 7.5h10.5M6.75 16.5h10.5" /><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 10.5h1.5v3h-1.5v-3zm0-3h1.5v3h-1.5V7.5zm15 3h1.5v3h-1.5v-3zm0-3h1.5v3h-1.5V7.5zM6.75 7.5v9m10.5-9v9" /></>)

export const UtensilsIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M12 8.25v-1.5m0 0a2.25 2.25 0 00-2.25 2.25v.75h4.5v-.75A2.25 2.25 0 0012 6.75zm0 0V3m-2.25 6h4.5v1.5a2.25 2.25 0 01-4.5 0V9zm2.25 3v9m-6-18v7.5a1.5 1.5 0 001.5 1.5h.75V21m0-18v7.5" />)

export const ClipboardIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H10.5A2.25 2.25 0 008.149 4.041M8.149 4.041A48.72 48.72 0 005.25 4.2c-1.131.094-1.976 1.057-1.976 2.192V16.5A2.25 2.25 0 005.25 18.75h2.018" />)

export const ChartBarIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />)

// Dashboard / status
export const FireIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />)

export const DropletIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M12 21.75c-3.723 0-6.75-3.136-6.75-6.375 0-4.078 5.197-11.012 6.324-12.47a.563.563 0 01.852 0C13.553 4.363 18.75 11.297 18.75 15.375c0 3.239-3.027 6.375-6.75 6.375z" />)

export const CogIcon = s(<><path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></>)

// Meal types
export const SunriseIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />)

export const SunIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />)

export const MoonIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />)

export const AppleIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M12 6.75c-1.5-2.25-4.5-3-6 0s-1.5 6 0 9 3 4.5 4.5 5.25c.75.375 1.125.375 1.5 0 1.5-.75 3-2.25 4.5-5.25s1.5-6.75 0-9-4.5-2.25-6 0zm0 0V3" />)

// Actions & states
export const PencilIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />)

export const TrophyIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-4.5A3.375 3.375 0 0019.875 10.5H21V6h-2.25a.75.75 0 01-.75-.75V3H6v2.25a.75.75 0 01-.75.75H3v4.5h1.125A3.375 3.375 0 017.5 14.25v4.5" />)

export const BoltIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />)

export const SparklesIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />)

export const GemIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M6 3l-3 6 9 12 9-12-3-6H6zM3 9h18M12 21L6 9m6 12l6-12M9 3l-3 6m12-6l-3 6" />)

export const CrownIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M3 18.75h18M3 18.75l1.5-12 4.5 4.5L12 5.25l3 6 4.5-4.5 1.5 12" />)

export const StarIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />)

export const MedalIcon = s(<><circle cx="12" cy="8" r="5" strokeLinecap="round" strokeLinejoin="round" /><path strokeLinecap="round" strokeLinejoin="round" d="M8.21 13.89L7 23l5-3 5 3-1.21-9.12" /></>)

export const TargetIcon = s(<><circle cx="12" cy="12" r="9" strokeLinecap="round" strokeLinejoin="round" /><circle cx="12" cy="12" r="5" strokeLinecap="round" strokeLinejoin="round" /><circle cx="12" cy="12" r="1" strokeLinecap="round" strokeLinejoin="round" /></>)

export const HeartIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />)

export const CheckCircleIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />)

export const ClockIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />)

export const PlayIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />)

export const PlusIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />)

export const ScaleIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1.5M18.364 5.636l-1.06 1.06M21 12h-1.5M18.364 18.364l-1.06-1.06M12 19.5V21M7.696 7.696l-1.06-1.06M4.5 12H3m3.696 6.364l1.06-1.06M12 16.5a4.5 4.5 0 100-9 4.5 4.5 0 000 9z" />)

export const FlameIcon = s(<path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />)

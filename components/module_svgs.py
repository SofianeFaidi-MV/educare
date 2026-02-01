def svg_intro_prog():
    return """
    <svg xmlns="http://www.w3.org/2000/svg" width="340" height="76" viewBox="0 0 340 76">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#0b1220"/>
          <stop offset="0.55" stop-color="#132a4d"/>
          <stop offset="1" stop-color="#0b1220"/>
        </linearGradient>
        <linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="#ffffff" stop-opacity="0.18"/>
          <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
        </linearGradient>
      </defs>

      <rect x="2" y="2" rx="18" width="336" height="72" fill="url(#bg)"/>
      <rect x="2" y="2" rx="18" width="336" height="72" fill="url(#sheen)"/>

      <text x="170" y="30" text-anchor="middle"
            font-size="14" font-weight="700" fill="#fff">
        420-111
      </text>

      <text x="170" y="52" text-anchor="middle"
            font-size="16" font-weight="800" fill="#fff">
        Introduction à la programmation
      </text>
    </svg>
    """

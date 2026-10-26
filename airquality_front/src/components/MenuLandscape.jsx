import { useEffect, useId, useState } from "react";
import { BirdSilhouette } from "./BirdSilhouette";
import "../assets/styles/menu_landscape.css";

// The water sits beneath both banks. Their shared contours cover the small
// underlap, so a resize never exposes a pale seam between land and water.
const lake = "M684 554C754 547 854 543 940 542L958 568 923 604 909 645 878 684C870 711 849 742 820 775H432L470 711 535 686 560 657 603 633 621 603 664 578Z";
const lakeBanks = "M696 558 674 584 631 609 613 639 570 663 545 693 483 717 447 760M886 531C902 540 922 545 926 556C936 571 919 584 911 599L897 641 866 680C858 706 837 733 810 760";
const flock = [[0, 0, 44], [54, -24, 36], [69, 28, 41], [112, -43, 31], [131, 51, 37], [174, 8, 32]];

export function MenuLandscape() {
  const unique = "menu-valley-" + useId().replaceAll(":", "");
  const [running, setRunning] = useState(true);

  useEffect(() => {
    const sync = () => setRunning(!document.hidden);
    sync();
    document.addEventListener("visibilitychange", sync);
    return () => document.removeEventListener("visibilitychange", sync);
  }, []);

  return <div className="menu-landscape" data-running={running} aria-hidden="true">
    <svg viewBox="0 0 1200 760" preserveAspectRatio="xMaxYMid slice" focusable="false">
      <defs>
        <clipPath id={`${unique}-lake`}><path d={lake} /></clipPath>
        <linearGradient id={`${unique}-water`} x1="0" y1="0" x2="0" y2="1">
          <stop className="menu-scene-water-far" offset="0" />
          <stop className="menu-scene-water-near" offset="1" />
        </linearGradient>
        <radialGradient id={`${unique}-water-light`} cx="42%" cy="38%" r="65%">
          <stop className="menu-scene-water-light" offset="0" stopOpacity=".34" />
          <stop className="menu-scene-water-light" offset="1" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`${unique}-mist`} x1="0" y1="0" x2="1" y2="1">
          <stop className="menu-scene-mist-top" offset="0" />
          <stop className="menu-scene-mist-bottom" offset="1" />
        </linearGradient>
      </defs>

      <g className="menu-scene-far-ridges">
        <path d="M6 576C69 540 103 511 152 491L219 432 249 444 310 383 342 400 397 341 431 359 473 329 528 382 571 405 622 452 675 462 748 532 818 583V760H6Z" />
        <path className="menu-scene-far-crease" d="m219 432 18 57 46 36m27-142-14 69-34 48m135-159-22 55-47 67m103-104 17 68 38 48m-4-146-11 70 16 24" />
      </g>

      <g className="menu-scene-high-ridge">
        <path d="M348 536C390 497 435 455 463 411L518 331 548 308 594 241 626 216 673 151Q687 134 701 151L734 170 768 214 800 234 841 293 880 323 928 389 975 438 1030 496 1056 551Z" />
        <path className="menu-scene-high-light" d="m673 151-30 107-42 51-29 85 65-45 34-73 24-52 32-48-26-25q-14-17-28 0Z" />
        <path className="menu-scene-high-shade" d="m701 151 32 114 44 44 19 66 43 40-29-109-42-92-34-44Z" />
        <path className="menu-scene-high-lines" d="m673 185-10 50-30 38-15 38m84-122 13 44 28 37 13 36m-74-29-7 66-22 39m69-66 17 39 9 37m-165 13-29 45-20 20m281-26 24 31 12 31" />
      </g>

      <path className="menu-scene-mist" d="M236 471C412 439 516 429 681 448S957 428 1114 463L1200 583H178Z" fill={`url(#${unique}-mist)`} />

      <g className="menu-scene-back-right">
        <path d="M690 525 744 468 786 449 823 400 856 387 892 332Q901 318 913 332L943 350 972 386 1006 401 1042 449 1091 477 1132 532L1128 580H674Z" />
        <path className="menu-scene-back-right-shade" d="m903 326-22 67-30 33 6 35-51 43 52-20 34-36 10-42 29-46Z" />
        <path className="menu-scene-back-right-line" d="m943 350-4 36 24 29 7 29m-147-44-6 38-36 33" />
      </g>

      <path className="menu-scene-lake" d={lake} fill={`url(#${unique}-water)`} />
      <g clipPath={`url(#${unique}-lake)`}>
        <ellipse className="menu-scene-water-reflection" cx="757" cy="654" rx="196" ry="102" fill={`url(#${unique}-water-light)`} />
        <path className="menu-scene-water-bank-reflection" d="M925 552C896 566 906 579 884 592C865 604 888 612 868 626C842 642 857 650 837 665C820 680 843 691 818 712L787 749 823 774H968V536ZM686 561C710 574 669 588 680 599C691 609 648 617 654 628C661 638 623 649 631 660C639 672 596 681 604 691L549 723 466 760 443 776H415L471 697 569 650 622 583Z" />
        <path className="menu-scene-water-contact" d={lakeBanks} />
        <path className="menu-scene-water-horizon" d="M684 554C754 547 854 543 940 542" />
        <g className="menu-scene-water-shift menu-scene-water-ripples-far" fill="none">
          <path d="M753 560c9-2 14 2 23 0s12-1 18 0M829 565l11-1 9 1 13-2M709 576c10-3 15 1 24 0l10-2M784 584l13-2 10 2 18-1M848 594c9-3 14 1 21-1M704 605l16-2 12 3 15-2M772 613c10-3 15 2 26 0l12-2" />
        </g>
        <g className="menu-scene-water-shift" fill="none">
          <path d="M658 628c14-5 21 2 34-1l17-3M811 637l17-3 13 2 16-2M710 653c14-4 22 4 34 1l20-4M607 674c14-4 23 2 36 0l19-4M759 686l19-4 17 3 24-2M651 708c16-5 25 3 41 0l20-4M552 733l19-3 19 4 26-4M730 744c17-5 27 4 42 0l24-3M621 766l20-4 15 3 20-2" />
        </g>
        <g className="menu-scene-water-shift menu-scene-water-shift-slow" fill="none">
          <path d="M778 573l10-1 8 1 12-1M739 594l12-2 8 1M750 634c12-3 18 2 27-1M670 653l15-2 11 1M776 664l18-2 12 2 15-2M692 690c13-3 20 2 31 0M586 711l14-2 11 2 17-3M655 737l19-3 14 3 20-2M526 759c14-3 23 3 39-1" />
        </g>
      </g>

      <g className="menu-scene-middle-left">
        <path d="M112 760C170 700 204 649 251 614L319 550 347 519 393 491 438 434 479 409 504 375Q514 358 526 374L546 390 560 425 591 453 607 487 643 508 657 540 696 558 674 584 631 609 613 639 570 663 545 693 483 717 447 760Z" />
        <path className="menu-scene-left-shadow" d="M251 614 319 550 347 519 393 491 438 434 479 409 504 375 489 424 463 448 470 474 438 503 419 531 438 555 408 584 368 607 343 648 304 677 299 717 248 760H112C170 700 204 649 251 614Z" />
        <path className="menu-scene-left-lit" d="m526 374 4 51 32 45 10 41 54 47-19-71-16-34-31-28-14-35Z" />
        <path className="menu-scene-left-lines" d="m493 410-12 31-27 24m62-66 8 44 28 31 7 35 27 25m-121-47-24 30-4 34-33 22m72-59 12 30 31 24 6 22m-162-9 25-22 20-32m69 74 31-13 11-23" />
      </g>

      <g className="menu-scene-front-right">
        <path d="M1206 760H810C837 733 858 706 866 680L897 641 911 599C919 584 936 571 926 556C922 545 902 540 886 531L846 502 864 471 895 450 920 408 948 384 970 340 1001 309 1020 270Q1027 252 1040 252L1057 272 1094 290 1119 327 1150 348 1173 392 1208 416Z" />
        <path className="menu-scene-front-shadow" d="M1040 252L1036 308 1004 355 996 408 954 444 945 486 896 516 886 531C902 540 922 545 926 556C936 571 919 584 911 599L897 641 866 680C858 706 837 733 810 760H927L973 696 977 658 1015 611 1006 566 1054 529 1058 486 1102 455 1088 400 1125 371 1106 327 1076 310 1059 277 1024 264Z" />
        <path className="menu-scene-front-lit" d="m1040 252 17 20 37 18 25 37 31 21-43-6-27-32-21-7-10-31Z" />
        <path className="menu-scene-front-lines" d="m1024 282-13 39-34 31-15 39-26 27m105-106-16 46-15 15-2 37-35 28m101-83-5 43-25 31 4 25-24 32m84-10-24 35 9 21-34 33m49-142 30 18 14 31m-202 64-27 19 29 17 15 22m35 26-27 32-3 27-30 22m140-70-37 36 3 34-40 29m-61 13-24 29-5 28m157-107-18 35 9 28-38 31" />
      </g>

      <g className="menu-scene-near-bank">
        <path d="M74 760C126 725 158 697 213 683C249 674 268 643 307 637C343 630 359 645 385 647C416 649 441 661 461 684C484 709 514 719 534 760Z" />
        <path className="menu-scene-near-grass" d="M247 728q5-36-10-57m17 52q16-35 12-58m-4 70q26-31 28-57m-18 61q28-22 37-47m-84 46q0-29-17-44m-25 64q8-39-5-63m22 61q17-34 17-52m121 66q-5-32-22-48m29 42q3-37-9-58m20 59q14-35 11-57m0 57q24-23 30-48" />
      </g>

      <g className="menu-scene-flock menu-scene-flock-near">
        {flock.map(([x, y, size], index) => <svg key={index} x={x} y={y} width={size} height={size * .64} viewBox="0 0 100 64" className="menu-scene-bird"
          style={{ "--bird-flap": `${340 + index * 13}ms`, "--bird-delay": `${-index * 137}ms` }}>
          <g transform="translate(100 0) scale(-1 1)"><BirdSilhouette variant={index % 3} /></g>
        </svg>)}
      </g>
      <g className="menu-scene-flock menu-scene-flock-far">
        {[[0, 0, 27], [-54, -26, 23], [-83, 22, 25]].map(([x, y, size], index) => <svg key={index} x={x} y={y} width={size} height={size * .64} viewBox="0 0 100 64" className="menu-scene-bird"
          style={{ "--bird-flap": `${370 + index * 17}ms`, "--bird-delay": `${-index * 213}ms` }}>
          <BirdSilhouette variant={(index + 1) % 3} />
        </svg>)}
      </g>
    </svg>
  </div>;
}

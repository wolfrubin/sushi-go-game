export interface Card {
    name: string;
}

export interface Player {
    name: string;
    hand?: Card[];
}

export interface SushiGame {
    name: string;
    players?: Player[];
}

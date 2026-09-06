import { ChangeDetectionStrategy, Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterLink } from '@angular/router';

interface Match {
  date: string;
  home: string;
  homeScore: string;
  away: string;
  awayScore: string;
  venue: string;
  year: string;
  ageGroup: string;
  competition: string;
}

interface LeagueRow {
  position: number;
  club: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  points: number;
}

interface Competition {
  name: string;
  url: string;
  year: string;
  ageGroup: string;
  table: LeagueRow[];
}

const matches: Match[] = [
  { date: '14 Sep 2025', home: "St. Jude's", homeScore: '2-14', away: 'Ballinteer St. Johns', awayScore: '1-11', venue: 'Parnell Park', year: '2025', ageGroup: 'Senior', competition: 'Dublin Senior Football Championship' },
  { date: '07 Sep 2025', home: 'Na Fianna', homeScore: '0-13', away: 'Clontarf', awayScore: '1-09', venue: 'O Tooles Park', year: '2025', ageGroup: 'Senior', competition: 'Dublin Senior Football Championship' },
  { date: '31 Aug 2025', home: 'Cuala', homeScore: '3-08', away: 'St. Brigids', awayScore: '2-12', venue: 'Pairc Ui Rinn', year: '2025', ageGroup: 'Senior', competition: 'Dublin Senior Football Championship' },
  { date: '22 Jun 2025', home: 'Raheny', homeScore: '1-10', away: 'Na Fianna', awayScore: '1-10', venue: 'St. Annes Park', year: '2025', ageGroup: 'Intermediate', competition: 'Dublin Intermediate Football League' },
  { date: '15 Jun 2025', home: 'Cuala', homeScore: '2-11', away: 'Raheny', awayScore: '0-08', venue: 'Dalkey', year: '2025', ageGroup: 'Intermediate', competition: 'Dublin Intermediate Football League' },
  { date: '14 Sep 2025', home: 'Raheny', homeScore: '1-12', away: 'Cuala', awayScore: '0-10', venue: 'St. Annes Park', year: '2025', ageGroup: 'Senior', competition: 'Dublin Senior Hurling Championship' },
  { date: '07 Sep 2025', home: 'Lucan Sarsfields', homeScore: '2-15', away: 'Naomh Barrog', awayScore: '1-09', venue: '12th Lock', year: '2025', ageGroup: 'Senior', competition: 'Dublin Senior Hurling Championship' }
];

const leagueRows: LeagueRow[] = [
  { position: 1, club: "St. Jude's", played: 5, won: 4, drawn: 0, lost: 1, points: 8 },
  { position: 2, club: 'Na Fianna', played: 5, won: 3, drawn: 1, lost: 1, points: 7 },
  { position: 3, club: 'Ballinteer St. Johns', played: 5, won: 3, drawn: 0, lost: 2, points: 6 },
  { position: 4, club: 'Clontarf', played: 5, won: 2, drawn: 1, lost: 2, points: 5 },
  { position: 5, club: 'Cuala', played: 5, won: 1, drawn: 1, lost: 3, points: 3 },
  { position: 6, club: 'St. Brigids', played: 5, won: 0, drawn: 1, lost: 4, points: 1 }
];

const intermediateLeagueRows: LeagueRow[] = [
  { position: 1, club: 'Cuala', played: 5, won: 4, drawn: 0, lost: 1, points: 8 },
  { position: 2, club: 'Raheny', played: 5, won: 3, drawn: 1, lost: 1, points: 7 },
  { position: 3, club: 'Na Fianna', played: 5, won: 2, drawn: 1, lost: 2, points: 5 },
  { position: 4, club: 'Clontarf', played: 5, won: 2, drawn: 0, lost: 3, points: 4 }
];

const seniorHurlingLeagueRows: LeagueRow[] = [
  { position: 1, club: 'Raheny', played: 5, won: 4, drawn: 0, lost: 1, points: 8 },
  { position: 2, club: 'Lucan Sarsfields', played: 5, won: 3, drawn: 1, lost: 1, points: 7 },
  { position: 3, club: 'Cuala', played: 5, won: 3, drawn: 0, lost: 2, points: 6 },
  { position: 4, club: 'Naomh Barrog', played: 5, won: 2, drawn: 1, lost: 2, points: 5 }
];

const competitions: Competition[] = [
  {
    name: 'Dublin Senior Football Championship',
    url: 'https://dublingaa.sportlomo.com/league-2/202576/',
    year: '2025',
    ageGroup: 'Senior',
    table: leagueRows
  },
  {
    name: 'Dublin Intermediate Football League',
    url: 'https://dublingaa.sportlomo.com/league-2/202577/',
    year: '2025',
    ageGroup: 'Intermediate',
    table: intermediateLeagueRows
  },
  {
    name: 'Dublin Senior Hurling Championship',
    url: 'https://dublingaa.sportlomo.com/league-2/202578/',
    year: '2025',
    ageGroup: 'Senior',
    table: seniorHurlingLeagueRows
  }
];

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [FormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatSelectModule, MatTableModule, MatToolbarModule, RouterLink],
  templateUrl: './results.component.html',
  styleUrl: './results.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ResultsComponent {
  readonly years = ['2025', '2024'];
  readonly ageGroups = ['Senior', 'Intermediate'];
  readonly competitionOptions = ['All competitions', ...competitions.map((competition) => competition.name)];
  readonly clubs = ['All clubs', "St. Jude's", 'Ballinteer St. Johns', 'Na Fianna', 'Clontarf', 'Cuala', 'St. Brigids', 'Raheny', 'Lucan Sarsfields', 'Naomh Barrog'];
  readonly selectedYear = signal('2025');
  readonly selectedAgeGroup = signal('Senior');
  readonly selectedCompetition = signal('All competitions');
  readonly selectedClub = signal('All clubs');
  readonly displayedColumns = ['position', 'club', 'played', 'won', 'drawn', 'lost', 'points'];

  readonly displayedLeagues = computed(() => {
    const competition = this.selectedCompetition();
    return competitions.filter((league) =>
      league.year === this.selectedYear() &&
      league.ageGroup === this.selectedAgeGroup() &&
      (competition === 'All competitions' || league.name === competition) &&
      (this.selectedClub() === 'All clubs' ||
        league.table.some((row) => row.club === this.selectedClub()))
    );
  });

  matchesFor(competition: Competition): Match[] {
    return matches.filter((match) =>
      match.year === competition.year &&
      match.ageGroup === competition.ageGroup &&
      match.competition === competition.name
    );
  }

  tableFor(competition: Competition): LeagueRow[] {
    return competition.table;
  }

  updateFilters(): void {
    // Signals keep the example data view immediately in sync with the selects.
  }
}

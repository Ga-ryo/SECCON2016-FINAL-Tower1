#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <malloc.h>
#include <linux/seccomp.h>
#include <sys/prctl.h>
#define BUFSIZE 1024
#define NONE 0
#define BLACK 1
#define WHITE 2


char banner[1024] = "  ____            _    ___ \n / ___| ___      / \\  |_ _|\n | |  _ / _ \\    / _ \\  | | \n | |_| | (_) |  / ___ \\ | | \n  \\____|\\___/  /_/   \\_\\___|";
extern struct _IO_FILE *stdin;
extern struct _IO_FILE *stdout;

void surrender(){puts("CMD:SURRENDER");}
void pass(){puts("CMD:PASS");}

void parseInput(char *input, char *buf, int isBoard){
  char *token;
  int i=0;
  if(input[0] !=  '['){
    puts("ERROR:Invalid format");
    exit(0);
  }
  input[0] = '\0';
  input++;
  if(input[strlen(input)-1] != ']'){
    puts("ERROR:Invalid format");
    exit(0);
  }
  input[strlen(input)-1] = '\0';
  token = strtok(input,",");
  while(token != NULL){
    if(isBoard){
      if(i%4==0)buf[i/4]=0;
      buf[i/4] += atoi(token)<<((i%4)*2);
      i++;
    }else{
      buf[i++] = (char)(atoi(token)-1);
    }
    token = strtok(NULL,",");
  }
}

int isPlayable(char input[2], char *board){
  int i;
  i = input[0]*19 + input[1];
  if((0x3&(board[i/4]>>((i%4)*2))) == 0)return 1;
  return 0;
}

void play(char input[2], char *board){
  char imitate[2];
  if(isPlayable("\x09\x09", board)){
    puts("CMD:PLAY\n[10,10]");
  }else{
    imitate[0] = (char)18 - input[0];
    imitate[1] = (char)18 - input[1];
    if(isPlayable(imitate, board)){
      printf("CMD:PLAY\n[%d,%d]\n",imitate[0]+1,imitate[1]+1);
    }else{
      pass();
    }
  }
}


/*
 * ^[.+,.+]$
 * [4,6] -> valid format
 * [4,5,1,23,4,23,3,62] -> valid and cause bug
 */
void main(){
  int i;
  char *s;
  char input[2];
  char *board;
  setvbuf(stdin,NULL,_IONBF,BUFSIZE);
  setvbuf(stdout,NULL,_IONBF,BUFSIZE);
  puts(banner);

  /* SLEEP */
  usleep(3000000);

  board = (char *)malloc(1024);
  s = (char *)malloc(2048);

  /* MODE 1 SECCOMP FILTER */
  prctl(PR_SET_SECCOMP, SECCOMP_MODE_STRICT);

  puts("CMD:GETINPUT");
  scanf("%2048[^\n]",s);getchar();
  parseInput(s, input, 0);
  puts("CMD:GETBOARD");
  scanf("%2048[^\n]",s);getchar();
  parseInput(s, board, 1);
  
  play(input, board);

  /* SURRENDER */
  puts("CMD:GETSCORE");
  read(0,s,128);
  if(atoi(s) <= -200){
    surrender();
  }
  exit(0);
}

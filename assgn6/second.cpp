#include <iostream>
#include <string>
#include <cmath>
using namespace std;

class Person {
protected:
    string name;
    int id;
public:
    Person (string n = "", int i = 0) {
    name = n ;
    id = i ;
    }
    void displayPerson ( ) {
    cout << "Name: " << name << endl ;
    cout << "ID : " << id << endl ;
    }
    ~Person() {
        cout << "Person Destroyed" << endl;
        // Destructor code if needed
    }

} ;

class Student : public Person{
    protected:
        string course;
        int semester;
        float marks[5];
    Student(string n , int i, string c , int s, float m[5]) : Person(n,i){
        course = c;
        semester = s;
        for(int i=0;i<5;i++){
            marks[i]=m[i];
        }
    }
    void displayStudent(){
        cout << "Course: " << course << endl;
        cout << "Semester: " << semester << endl;
        cout << "Marks: ";
        for(int i=0;i<5;i++){
            cout << marks[i] << " ";
        }
        cout << endl;
    }
    ~Student() {
        cout << "Student Destroyed" << endl;
        // Destructor code if needed
    }   
};
class Sports: public Person{
protected:
    int sportsMarks;
    Sports(string n, int i, int sm) : Person(n,i){
        sportsMarks = sm;
    }
    void displaySports(){
        cout << "Sports Marks: " << sportsMarks << endl;
    }
    void display(){
        displayPerson();
    }
    ~Sports() {
        cout << "Sports Destroyed" << endl;
        // Destructor code if needed
    }
    
};

class Result : public Student, public Sports{
    private:
        int total;
        float average;
        char grade;
    public:
    Result(string n, int i, int sm, string c , int s , float m[5]) : Student(n,i,c,s,m), Sports(n,i,sm){
        total = 0;
        average = 0;
        grade = 'A';
    }
    void calculateResult(void){
        for(int i=0;i<5;i++){
            total += marks[i];
        }
        total = total + sportsMarks;
        average = total / 6.0;
        if(average>=90){
            grade = 'A';
        }else if(average>=75){
            grade = 'B';
        }else if(average>=60){
            grade = 'C';
        }else if(average>=45){
            grade = 'D';
        }else{
            grade = 'F';    
        }
    }
    void displayResult(){
        display();
        displayStudent();
        displaySports();
        cout << "Total Marks: " << total << endl;
        cout << "Average Marks: " << average << endl;
        cout << "Grade: " << grade << endl;
    }
    ~Result() {
        cout << "Result Destroyed" << endl;
        // Destructor code if needed
    }
};

int main() {

    int sttotal;
    cout << "Enter number of students: ";
    cin >> sttotal;

    Result* students = new Result[sttotal];   // dynamic array

    for(int i=0;i<sttotal;i++){

        string name, course;
        int id, semester, sportsMarks;
        float marks[5];

        cout << "\nEnter details for Student " << i+1 << endl;

        cout << "Enter Name and ID: ";
        cin >> name >> id;

        cout << "Enter Course and Semester: ";
        cin >> course >> semester;

        cout << "Enter marks for 5 subjects: ";
        for(int j=0;j<5;j++)
            cin >> marks[j];

        cout << "Enter Sports Marks: ";
        cin >> sportsMarks;

        students[i] = Result(name,id,sportsMarks,course,semester,marks);

        students[i].calculateResult();
    }

    cout << "\nAll Students Report\n";

    for(int i=0;i<sttotal;i++){

        cout << "\nStudent " << i+1 << ":\n";

        students[i].displayResult();
    }

    delete[] students;  // destructors called here
}
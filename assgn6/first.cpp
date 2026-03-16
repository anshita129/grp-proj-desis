#include <iostream>
#include <string>
#include <cmath>
using namespace std;
class Polar {
private:
    float r;
    float a;
public :

Polar (float radius=0, float angle=0) {
    r=radius ;
    a=angle ;
}
Polar operator+(Polar p){
    Polar temp;
    float x = r*cos(a*3.14/180) + p.r*cos(p.a*3.14/180);
    float y = r*sin(a*3.14/180) + p.r*sin(p.a*3.14/180);
    temp.r = sqrt(x*x + y*y);
    temp.a = atan2(y, x) * 180 / 3.14;
    return temp;
}

void display ( ) {
    cout << "Radius=" << r << " Angle=" << a << " degrees" << endl;
} };

int main ( ) {
    int r1, a1;
    cin >> r1 >> a1 ;
    Polar p1 (r1, a1) ;
    int r2,a2;
    cin >> r2 >> a2 ;
    Polar p2 (r2, a2) ;

    p1.display ( ) ;
    p2.display ( ) ;
    Polar p3 = p1 + p2 ;
    p3.display ( ) ;
    return  0 ;
}